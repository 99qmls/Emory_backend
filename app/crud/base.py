from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import BaseModel as DBBaseModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Union[int, UUID]) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        stmt = select(self.model)

        # 🔹 动态生成 filters 条件
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        # 🔹 排序
        if order_by:
            col_name = order_by.lstrip("-")
            column = getattr(self.model, col_name, None)
            if column is not None:
                if order_by.startswith("-"):
                    stmt = stmt.order_by(column.desc())
                else:
                    stmt = stmt.order_by(column.asc())
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict() if isinstance(obj_in, BaseModel) else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        # await db.refresh(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Union[int, UUID], soft: bool = True) -> Optional[ModelType]:
        obj = await self.get(db, id=id)
        if obj:
            if soft:
                obj.is_deleted = True
                db.add(obj)
            else:
                await db.delete(obj)
            await db.commit()
        return obj