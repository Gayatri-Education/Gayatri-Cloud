"""Event Management, Archiving, and Training Governance API Endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleEnum, TenantContext, resolve_tenant_context
from app.core.storage import get_storage_service
from app.db.models.events import EventArchiveBatch, TrainingDatasetExport
from app.db.session import get_db
from app.domain.events.archiver import ArchiveService
from app.domain.events.outbox import OutboxService
from app.domain.events.training import TrainingPipelineService

router = APIRouter(prefix="/events", tags=["events"])


class ProcessOutboxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_size: int = Field(default=50, ge=1, le=500)


class TrainingEligibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    user_consented: bool
    institution_authorized: bool
    authorization_basis: str = "EXPLICIT_CONSENT"


class ExportDatasetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_tag: str
    train_ratio: float = Field(default=0.80, gt=0.0, lt=1.0)
    val_ratio: float = Field(default=0.10, gt=0.0, lt=1.0)
    test_ratio: float = Field(default=0.10, gt=0.0, lt=1.0)


@router.post("/outbox/process")
async def process_outbox(
    req: ProcessOutboxRequest = ProcessOutboxRequest(),
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Process pending outbox events into immutable S3 batches (Admin only)."""
    if not context.has_role(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger outbox archiving.",
        )

    storage = get_storage_service()
    batch = await ArchiveService.process_pending_outbox(
        session=db, storage_service=storage, batch_size=req.batch_size
    )
    if not batch:
        return {"status": "idle", "archived_count": 0, "batch": None}

    return {
        "status": "processed",
        "archived_count": batch.event_count,
        "batch_id": batch.batch_id,
        "storage_path": batch.storage_path,
        "sha256": batch.sha256_checksum,
    }


@router.get("/outbox/status")
async def get_outbox_status(
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get transactional outbox queue statistics and lag."""
    return await OutboxService.get_queue_stats(db)


@router.get("/archive/batches")
async def list_archive_batches(
    limit: int = 50,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List archived batches and checksums."""
    stmt = select(EventArchiveBatch).order_by(EventArchiveBatch.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    batches = res.scalars().all()
    return [
        {
            "id": b.id,
            "batch_id": b.batch_id,
            "storage_path": b.storage_path,
            "sha256": b.sha256_checksum,
            "event_count": b.event_count,
            "manifest": json.loads(b.manifest_json),
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batches
    ]


@router.post("/training/eligibility")
async def set_training_eligibility(
    req: TrainingEligibilityRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate training eligibility for an event under deny-by-default governance."""
    if not context.has_role(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can govern training eligibility.",
        )

    record = await TrainingPipelineService.evaluate_eligibility(
        session=db,
        event_id=req.event_id,
        user_consented=req.user_consented,
        institution_authorized=req.institution_authorized,
        authorization_basis=req.authorization_basis,
        reviewer_id=context.user.id,
    )
    return {
        "event_id": record.event_id,
        "status": record.status,
        "authorization_basis": record.authorization_basis,
        "pii_redacted": record.pii_redacted,
        "exclusion_reason": record.exclusion_reason,
    }


@router.post("/training/export", status_code=status.HTTP_201_CREATED)
async def export_training_dataset(
    req: ExportDatasetRequest,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a reproducible training dataset export manifest from eligible records."""
    if not context.has_role(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can export training datasets.",
        )

    export_rec = await TrainingPipelineService.export_dataset(
        session=db,
        version_tag=req.version_tag,
        train_ratio=req.train_ratio,
        val_ratio=req.val_ratio,
        test_ratio=req.test_ratio,
    )
    return {
        "id": export_rec.id,
        "version_tag": export_rec.version_tag,
        "total_examples": export_rec.total_examples,
        "train_count": export_rec.train_count,
        "val_count": export_rec.val_count,
        "test_count": export_rec.test_count,
        "sha256": export_rec.sha256_checksum,
        "is_approved": export_rec.is_approved,
    }


@router.post("/training/datasets/{dataset_id}/approve")
async def approve_training_dataset(
    dataset_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Admin human approval gate permitting dataset to be used in training."""
    if not context.has_role(RoleEnum.ORG_ADMIN.value, RoleEnum.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can approve training datasets.",
        )

    approved = await TrainingPipelineService.approve_dataset(
        session=db, dataset_id=dataset_id, approver_id=context.user.id
    )
    return {
        "id": approved.id,
        "version_tag": approved.version_tag,
        "is_approved": approved.is_approved,
        "approved_by": approved.approved_by,
        "approved_at": approved.approved_at.isoformat() if approved.approved_at else None,
    }


@router.get("/training/datasets")
async def list_training_datasets(
    context: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List dataset exports and their human approval statuses."""
    stmt = select(TrainingDatasetExport).order_by(TrainingDatasetExport.created_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "version_tag": r.version_tag,
            "total_examples": r.total_examples,
            "train_count": r.train_count,
            "val_count": r.val_count,
            "test_count": r.test_count,
            "sha256": r.sha256_checksum,
            "is_approved": r.is_approved,
            "approved_by": r.approved_by,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
        }
        for r in records
    ]
