"""
Base repository for database operations.

This module defines a generic `BaseRepository` class that provides
common database operations for SQLAlchemy models. It includes methods
for retrieving, creating, updating, and deleting records in the database.

Classes:
    BaseRepository: A generic repository for performing CRUD operations.
"""

from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    """A generic repository for performing CRUD operations on SQLAlchemy models.

    This class provides common database operations such as retrieving all records,
    retrieving a record by ID, creating a new record, updating an existing record,
    and deleting a record.

    Attributes:
        db (AsyncSession): The database session.
        model (Type[ModelType]): The SQLAlchemy model associated with the repository.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]) -> None:
        """Initializes the repository with a database session and model.

        Args:
            session (AsyncSession): The database session.
            model (Type[ModelType]): The SQLAlchemy model associated with the repository.
        """
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        """Retrieves all records of the model from the database.

        Returns:
            list[ModelType]: A list of all records of the model.
        """
        stmt = select(self.model)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        """Retrieves a record by its ID.

        Args:
            _id (int): The ID of the record to retrieve.

        Returns:
            ModelType | None: The record with the specified ID, or None if not found.
        """
        stmt = select(self.model).filter_by(id=_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, instance: ModelType) -> ModelType:
        """Creates a new record in the database.

        Args:
            instance (ModelType): The instance of the model to create.

        Returns:
            ModelType: The created instance with updated fields (e.g., ID).
        """
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Updates an existing record in the database.

        Args:
            instance (ModelType): The instance of the model to update.

        Returns:
            ModelType: The updated instance.
        """
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Deletes a record from the database.

        Args:
            instance (ModelType): The instance of the model to delete.
        """
        await self.db.delete(instance)
        await self.db.commit()
