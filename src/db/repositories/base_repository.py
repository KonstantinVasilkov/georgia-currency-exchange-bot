"""
Base repository for database operations.

This module provides a base repository class for database operations.
It implements common CRUD operations that can be used by specific repositories.
"""

from typing import Generic, TypeVar, Type, Optional, Any, Dict, Union, Sequence
from sqlmodel import SQLModel, select, Session

# Define a type variable for the model
T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """
    Base repository for database operations.

    This class provides common CRUD operations for database models.
    It is designed to be subclassed by specific repositories.

    Attributes:
        model_class: The SQLModel class that this repository operates on.
    """

    def __init__(self, model_class: Type[T]):
        """
        Initialize the repository with a model class.

        Args:
            model_class: The SQLModel class that this repository operates on.
        """
        self.model_class = model_class

    def create(self, session: Session, obj_in: Union[Dict[str, Any], T]) -> T:
        """
        Create a new record in the database.

        Args:
            session: The database session.
            obj_in: The data to create the record with. Can be a dict or a model instance.

        Returns:
            The created record.
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
            db_obj = self.model_class(**obj_in_data)  # type: ignore
        else:
            db_obj = obj_in

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def get(self, session: Session, id: Any) -> Optional[T]:
        """
        Get a record by ID.

        Args:
            session: The database session.
            id: The ID of the record to get.

        Returns:
            The record if found, None otherwise.
        """
        return session.get(self.model_class, id)

    def get_multi(
        self, session: Session, *, skip: int = 0, limit: int = 100
    ) -> Sequence[T]:
        """
        Get multiple records.

        Args:
            session: The database session.
            skip: The number of records to skip.
            limit: The maximum number of records to return.

        Returns:
            A list of records.
        """
        statement = select(self.model_class).offset(skip).limit(limit)
        return session.exec(statement).all()

    def update(
        self, session: Session, *, db_obj: T, obj_in: Union[Dict[str, Any], T]
    ) -> T:
        """
        Update a record.

        Args:
            session: The database session.
            db_obj: The record to update.
            obj_in: The data to update the record with. Can be a dict or a model instance.

        Returns:
            The updated record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def delete(self, session: Session, *, id: Any) -> Optional[T]:
        """
        Delete a record by ID.

        Args:
            session: The database session.
            id: The ID of the record to delete.

        Returns:
            The deleted record if found, None otherwise.
        """
        obj = session.get(self.model_class, id)
        if obj:
            session.delete(obj)
            session.commit()
        return obj

    def exists(self, session: Session, **kwargs) -> bool:
        """
        Check if a record exists with the given criteria.

        Args:
            session: The database session.
            **kwargs: The criteria to check for.

        Returns:
            True if a record exists, False otherwise.
        """
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)

        result = session.exec(statement).first()
        return result is not None

    def find_by(self, session: Session, **kwargs) -> Sequence[T]:
        """
        Find records by criteria.

        Args:
            session: The database session.
            **kwargs: The criteria to search for.

        Returns:
            A list of records matching the criteria.
        """
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)

        return session.exec(statement).all()

    def find_one_by(self, session: Session, **kwargs) -> Optional[T]:
        """
        Find a single record by criteria.

        Args:
            session: The database session.
            **kwargs: The criteria to search for.

        Returns:
            The first record matching the criteria, or None if no record is found.
        """
        statement = select(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                statement = statement.where(getattr(self.model_class, key) == value)

        return session.exec(statement).first()
