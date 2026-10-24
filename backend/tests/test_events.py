"""Comprehensive test suite for Event Capture, Archiving, Telemetry, and Training Pipeline (Phase P11)."""

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.storage import get_storage_service
from app.db.base import Base
from app.db.session import get_db
from app.domain.events.archiver import ArchiveService
from app.domain.events.envelope import (
    EventEnvelope,
    SensitivityLevel,
)
from app.domain.events.outbox import OutboxService
from app.domain.events.telemetry import OperationalTelemetry
from app.domain.events.training import PIIRedactor, TrainingPipelineService
from app.main import app


@pytest.fixture
async def events_test_client():
    """Provides AsyncClient with an isolated in-memory test database."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def register_and_login(client: AsyncClient, email: str, full_name: str) -> tuple[dict, str]:
    """Helper to register and login a user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    user_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return user_res.json(), token


# --- 1. Unit Tests: Envelope, Outbox, Telemetry, and PII Redaction ---


def test_canonical_event_envelope():
    env = EventEnvelope(
        event_type="tutor.turn_completed",
        schema_version="1.0.0",
        actor_id="usr_123",
        organization_id="org_456",
        session_id="ses_789",
        correlation_id="corr_abc",
        sensitivity_level=SensitivityLevel.PROTECTED,
        payload={"query": "Explain gravity", "response": "Gravity is..."},
    )
    d = env.to_dict()
    assert d["event_type"] == "tutor.turn_completed"
    assert d["schema_version"] == "1.0.0"
    assert d["sensitivity_level"] == "PROTECTED"
    assert "timestamp_utc" in d

    recovered = EventEnvelope.from_dict(d)
    assert recovered.event_id == env.event_id
    assert recovered.payload["query"] == "Explain gravity"


def test_pii_redactor():
    raw_text = (
        "Contact Alice at alice@example.com or phone +1-555-123-4567. Server IP is 192.168.1.50."
    )
    scrubbed = PIIRedactor.redact_text(raw_text)
    assert "alice@example.com" not in scrubbed
    assert "[EMAIL_REDACTED]" in scrubbed
    assert "+1-555-123-4567" not in scrubbed
    assert "[PHONE_REDACTED]" in scrubbed
    assert "192.168.1.50" not in scrubbed
    assert "[IP_REDACTED]" in scrubbed

    nested = {
        "user": {"email": "student@school.edu", "details": "Call 800-555-0199"},
        "active": True,
    }
    scrubbed_obj = PIIRedactor.redact_object(nested)
    assert scrubbed_obj["user"]["email"] == "[EMAIL_REDACTED]"
    assert "[PHONE_REDACTED]" in scrubbed_obj["user"]["details"]


def test_operational_telemetry_redaction():
    dangerous_meta = {
        "prompt": "SELECT * FROM secrets",
        "student_response": "My password is secret",
        "api_key": "sk-live-secret-key-12345",
        "latency_ms": 125.4,
        "model": "gpt-4o",
    }
    telemetry = OperationalTelemetry.format_telemetry_entry(
        component="AIGateway",
        event_type="ai.completion_served",
        correlation_id="corr_999",
        extra_metadata=dangerous_meta,
    )
    assert telemetry["component"] == "AIGateway"
    assert telemetry["metadata"]["prompt"] == "[REDACTED]"
    assert telemetry["metadata"]["student_response"] == "[REDACTED]"
    assert telemetry["metadata"]["api_key"] == "[REDACTED]"
    assert telemetry["metadata"]["latency_ms"] == 125.4


@pytest.mark.asyncio
async def test_transactional_outbox_and_quarantine(events_test_client: AsyncClient):
    # Fetch DB session via app dependency
    from app.db.session import get_db

    async for session in app.dependency_overrides[get_db]():
        # 1. Record event in transactional outbox
        envelope = EventEnvelope(
            event_type="course.version_published",
            payload={"course_id": "c1", "version": "v1.0.0"},
            actor_id="u1",
            organization_id="org1",
        )
        app_event = await OutboxService.record_event(session, envelope)
        await session.commit()

        # Verify ApplicationEvent and EventOutbox recorded
        pending = await OutboxService.get_pending_batch(session)
        assert len(pending) >= 1
        outbox_item, fetched_event = pending[0]
        assert fetched_event.id == app_event.id
        assert outbox_item.status == "pending"

        # 2. Simulate failure retries up to quarantine
        await OutboxService.record_failure(
            session, outbox_item.id, "Network timeout 1", max_retries=3
        )
        await session.commit()
        await session.refresh(outbox_item)
        assert outbox_item.retry_count == 1
        assert outbox_item.status == "failed"

        await OutboxService.record_failure(
            session, outbox_item.id, "Network timeout 2", max_retries=3
        )
        await session.commit()
        await session.refresh(outbox_item)
        assert outbox_item.retry_count == 2
        assert outbox_item.status == "failed"

        # 3rd failure -> Quarantine
        await OutboxService.record_failure(
            session, outbox_item.id, "Fatal poison event", max_retries=3
        )
        await session.commit()
        await session.refresh(outbox_item)
        assert outbox_item.retry_count == 3
        assert outbox_item.status == "quarantined"

        stats = await OutboxService.get_queue_stats(session)
        assert stats["quarantined"] >= 1


@pytest.mark.asyncio
async def test_archive_service_batching_and_checksum_integrity(events_test_client: AsyncClient):
    from app.db.session import get_db

    async for session in app.dependency_overrides[get_db]():
        storage = get_storage_service()

        # Enqueue 3 events
        for i in range(3):
            env = EventEnvelope(
                event_type="tutor.turn_completed",
                payload={"turn": i, "content": f"Sample turn content {i}"},
            )
            await OutboxService.record_event(session, env)
        await session.commit()

        # Archive pending outbox
        batch = await ArchiveService.process_pending_outbox(session, storage, batch_size=10)
        assert batch is not None
        assert batch.event_count >= 3
        assert len(batch.sha256_checksum) == 64

        # Verify integrity against storage
        is_valid = await ArchiveService.verify_batch_integrity(session, storage, batch.batch_id)
        assert is_valid is True

        # Second run should find 0 pending events
        empty_batch = await ArchiveService.process_pending_outbox(session, storage, batch_size=10)
        assert empty_batch is None


@pytest.mark.asyncio
async def test_training_governance_and_export_splits(events_test_client: AsyncClient):
    from app.db.session import get_db

    async for session in app.dependency_overrides[get_db]():
        # Enqueue events
        e1 = await OutboxService.record_event(
            session,
            EventEnvelope(
                event_type="tutor.turn_completed",
                payload={"student_input": "What is momentum?", "contact": "alice@test.org"},
            ),
        )
        e2 = await OutboxService.record_event(
            session,
            EventEnvelope(
                event_type="tutor.turn_completed",
                payload={"student_input": "How does force relate?", "contact": "bob@test.org"},
            ),
        )
        await session.commit()

        # 1. Deny-by-default: E1 is excluded due to lack of consent
        rec1 = await TrainingPipelineService.evaluate_eligibility(
            session=session,
            event_id=e1.id,
            user_consented=False,
            institution_authorized=True,
        )
        assert rec1.status == "EXCLUDED"
        assert "Missing" in rec1.exclusion_reason or "Denied" in rec1.exclusion_reason

        # 2. Approved consent and policy: E2 is marked ELIGIBLE
        rec2 = await TrainingPipelineService.evaluate_eligibility(
            session=session,
            event_id=e2.id,
            user_consented=True,
            institution_authorized=True,
        )
        assert rec2.status == "ELIGIBLE"
        assert rec2.pii_redacted is True

        # 3. Export dataset containing only eligible records
        export_rec = await TrainingPipelineService.export_dataset(
            session=session,
            version_tag="dataset_tutor_v1",
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
        )
        assert export_rec.total_examples == 1
        assert export_rec.is_approved is False

        # 4. Gating check: Unapproved dataset cannot be used for training
        with pytest.raises(HTTPException):
            await TrainingPipelineService.verify_training_allowed(session, export_rec.id)

        # 5. Human approval gate
        approved = await TrainingPipelineService.approve_dataset(
            session=session, dataset_id=export_rec.id, approver_id="admin_chief"
        )
        assert approved.is_approved is True
        assert approved.approved_by == "admin_chief"

        # Now verification passes
        assert await TrainingPipelineService.verify_training_allowed(session, export_rec.id) is True


# --- 2. End-to-End API Integration Tests ---


@pytest.mark.asyncio
async def test_events_api_end_to_end(events_test_client: AsyncClient):
    # 1. Register Admin and Organization
    admin_user, admin_token = await register_and_login(
        events_test_client, "admin.events@example.internal", "Admin Events"
    )
    org_res = await events_test_client.post(
        "/api/v1/organizations",
        json={"name": "Event Data Org", "slug": "event-data-org"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org_id}

    # 2. Check outbox queue status
    status_res = await events_test_client.get("/api/v1/events/outbox/status", headers=admin_headers)
    assert status_res.status_code == 200
    assert "pending" in status_res.json()

    # 3. Add an event to outbox via backend session
    from app.db.session import get_db

    event_id = None
    async for session in app.dependency_overrides[get_db]():
        app_ev = await OutboxService.record_event(
            session,
            EventEnvelope(
                event_type="learning.concept_mastered",
                payload={"concept": "conservation_of_energy", "student": "carol@test.internal"},
                organization_id=org_id,
            ),
        )
        await session.commit()
        event_id = app_ev.id

    # 4. Process outbox via API
    proc_res = await events_test_client.post(
        "/api/v1/events/outbox/process",
        headers=admin_headers,
        json={"batch_size": 20},
    )
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "processed"
    assert proc_res.json()["archived_count"] >= 1

    # 5. List archive batches
    batches_res = await events_test_client.get(
        "/api/v1/events/archive/batches", headers=admin_headers
    )
    assert batches_res.status_code == 200
    assert len(batches_res.json()) >= 1
    assert "sha256" in batches_res.json()[0]

    # 6. Set training eligibility
    elig_res = await events_test_client.post(
        "/api/v1/events/training/eligibility",
        headers=admin_headers,
        json={
            "event_id": event_id,
            "user_consented": True,
            "institution_authorized": True,
            "authorization_basis": "INSTITUTION_POLICY",
        },
    )
    assert elig_res.status_code == 200
    assert elig_res.json()["status"] == "ELIGIBLE"

    # 7. Export training dataset
    export_res = await events_test_client.post(
        "/api/v1/events/training/export",
        headers=admin_headers,
        json={"version_tag": "dataset_v1_api"},
    )
    assert export_res.status_code == 201
    dataset_id = export_res.json()["id"]
    assert export_res.json()["is_approved"] is False

    # 8. Human approval gate
    appr_res = await events_test_client.post(
        f"/api/v1/events/training/datasets/{dataset_id}/approve",
        headers=admin_headers,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["is_approved"] is True

    # 9. List datasets
    list_ds = await events_test_client.get(
        "/api/v1/events/training/datasets", headers=admin_headers
    )
    assert list_ds.status_code == 200
    assert len(list_ds.json()) >= 1
    assert list_ds.json()[0]["is_approved"] is True
