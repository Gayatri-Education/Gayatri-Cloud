"""Tenant-Scoped Repository interfaces enforcing strict data isolation."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    """Generic base repository for global entities."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: str) -> ModelT | None:
        """Fetch entity by primary key."""
        result = await self.session.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> ModelT:
        """Create and add a new entity."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance


class BaseTenantRepository[ModelT: Base]:
    """Tenant-scoped repository enforcing organization boundary predicates on all operations."""

    def __init__(self, model: type[ModelT], session: AsyncSession, organization_id: str) -> None:
        if not organization_id:
            raise ValueError("organization_id must be provided for tenant-scoped operations")
        self.model = model
        self.session = session
        self.organization_id = organization_id

    async def get_by_id(self, entity_id: str) -> ModelT | None:
        """Fetch entity by primary key strictly constrained to the active organization."""
        query = select(self.model).where(
            self.model.id == entity_id,
            self.model.organization_id == self.organization_id,
        )
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """List entities for the tenant with pagination."""
        query = select(self.model).where(self.model.organization_id == self.organization_id)
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted.is_(False))

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelT:
        """Create entity with organization_id strictly bound."""
        kwargs["organization_id"] = self.organization_id
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def soft_delete(self, entity_id: str) -> bool:
        """Soft-delete an entity strictly within tenant boundary."""
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError(f"Model {self.model.__name__} does not support soft delete")

        stmt = (
            update(self.model)
            .where(
                self.model.id == entity_id,
                self.model.organization_id == self.organization_id,
            )
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
