"""
Base repository for database operations.

This module provides a base repository class for database operations.
It implements common CRUD operations that can be used by specific repositories.
"""

from typing import Generic, TypeVar, Type, Optional, Any, Dict, Union, Sequence
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

# Define a type variable for the model
T = TypeVar("T", bound=SQLModel)


class AsyncBaseRepository(Generic[T]):
    """
    Async base repository for database operations.
    Provides async CRUD operations for database models.
    """

    def __init__(self, model_class: Type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session

    async def create(self, obj_in: Union[Dict[str, Any], T]) -> T:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
            db_obj = self.model_class(**obj_in_data)  # type: ignore
        else:
            db_obj = obj_in
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def get(self, id: Any) -> Optional[T]:
        return await self.session.get(self.model_class, id)

    async def get_multi(self, *, offset: int = 0, limit: int = 100) -> Sequence[T]:
        statement = select(self.model_class).offset(offset).limit(limit)
        result = await self.session.exec(statement)
        return result.all()

    async def update(self, *, db_obj: T, obj_in: Union[Dict[str, Any], T]) -> T:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: Any) -> Optional[T]:
        obj = await self.session.get(self.model_class, id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj

    async def exists(self, **kwargs) -> bool:
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)
        result = await self.session.exec(statement)
        return result.first() is not None

    async def find_by(self, **kwargs) -> Sequence[T]:
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)
        result = await self.session.exec(statement)
        return result.all()

    async def find_one_by(self, **kwargs) -> Optional[T]:
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)
        result = await self.session.exec(statement)
        return result.first()
