"""Comprehensive test suite for tutoring benchmark, model eligibility, and quality-first routing."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.domain.benchmarks.benchmark_suite import TutoringBenchmarkSuite
from app.main import app


@pytest.fixture
async def bench_test_client() -> AsyncClient:
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


# --- 1. Unit Tests: Benchmark Suite and Evaluator ---


def test_benchmark_suite_structure():
    """Verify benchmark suite has comprehensive pedagogical and safety test cases."""
    cases = TutoringBenchmarkSuite.get_test_cases()
    assert len(cases) >= 5

    task_types = {c.task_type for c in cases}
    assert "socratic_scaffolding" in task_types
    assert "concept_explanation" in task_types
    assert "misconception_diagnosis" in task_types
    assert "math_reasoning" in task_types
    assert "safety_resistance" in task_types


@pytest.mark.asyncio
async def test_benchmark_evaluator_scoring(bench_test_client: AsyncClient):
    """Verify evaluator scores model, evaluates eligibility, and persists ModelBenchmarkRun."""
    # Obtain session through app dependency
    user, token = await register_and_login(
        bench_test_client, "bench.admin@example.internal", "Bench Admin"
    )
    auth_header = {"Authorization": f"Bearer {token}"}

    org_res = await bench_test_client.post(
        "/api/v1/organizations",
        json={"name": "Eval Academy", "slug": "eval-acad"},
        headers=auth_header,
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # Execute benchmark run via API
    run_res = await bench_test_client.post(
        "/api/v1/benchmarks/run",
        json={"provider_type": "mock", "model_id": "mock-tutor-standard"},
        headers=headers,
    )
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["model_id"] == "mock-tutor-standard"
    assert run_data["composite_score"] > 0.0
    assert run_data["safety_score"] >= 80.0
    assert run_data["benchmark_suite_version"] == TutoringBenchmarkSuite.SUITE_VERSION

    # List runs
    list_res = await bench_test_client.get("/api/v1/benchmarks/runs", headers=headers)
    assert list_res.status_code == 200
    runs = list_res.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == run_data["id"]


# --- 2. Intelligent Routing Tests ---


@pytest.mark.asyncio
async def test_quality_first_routing(bench_test_client: AsyncClient):
    """Verify router selects highest-scoring benchmarked model."""
    user, token = await register_and_login(
        bench_test_client, "learner.route@example.internal", "Learner Route"
    )
    org_res = await bench_test_client.post(
        "/api/v1/organizations",
        json={"name": "Route Academy", "slug": "route-acad"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 1. Run benchmark for model A (Standard)
    await bench_test_client.post(
        "/api/v1/benchmarks/run",
        json={"provider_type": "mock", "model_id": "mock-tutor-standard"},
        headers=headers,
    )

    # 2. Route task (should select the evaluated eligible model)
    route_res = await bench_test_client.post(
        "/api/v1/benchmarks/route",
        json={"task_type": "tutoring", "min_context_window": 4096},
        headers=headers,
    )
    assert route_res.status_code == 200
    decision = route_res.json()
    assert decision["selected_model"] == "mock-tutor-standard"
    assert decision["is_manual_override"] is False
    assert decision["composite_score"] > 0


@pytest.mark.asyncio
async def test_manual_override_routing(bench_test_client: AsyncClient):
    """Verify manual override is respected when valid, and rejected if context limit fails."""
    user, token = await register_and_login(
        bench_test_client, "override.user@example.internal", "Override User"
    )
    org_res = await bench_test_client.post(
        "/api/v1/organizations",
        json={"name": "Override Org", "slug": "override-org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = org_res.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # Sync model snapshots
    await bench_test_client.post("/api/v1/ai/models/sync?provider_type=mock", headers=headers)

    # Manual override to mock-fast-evaluator
    route_res = await bench_test_client.post(
        "/api/v1/benchmarks/route",
        json={
            "task_type": "tutoring",
            "requested_model_id": "mock-fast-evaluator",
            "min_context_window": 2048,
        },
        headers=headers,
    )
    assert route_res.status_code == 200
    decision = route_res.json()
    assert decision["selected_model"] == "mock-fast-evaluator"
    assert decision["is_manual_override"] is True

    # Manual override with excessive context requirement (MUST FAIL with 400)
    fail_res = await bench_test_client.post(
        "/api/v1/benchmarks/route",
        json={
            "task_type": "tutoring",
            "requested_model_id": "mock-fast-evaluator",
            "min_context_window": 100000,
        },
        headers=headers,
    )
    assert fail_res.status_code == 400
    assert "context window" in fail_res.json()["detail"].lower()
