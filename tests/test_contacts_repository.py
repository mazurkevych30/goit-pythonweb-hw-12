"""
Unit tests for the ContactsRepository class.

This module contains test cases for various methods of the ContactsRepository class,
including creating, updating, retrieving, and deleting contacts, as well as searching
and retrieving upcoming birthdays. The tests use pytest and mock objects to simulate
the behavior of the database and repository methods.
"""

from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactsRepository
from src.schemas.contacts import BaseContact, UpdateContact


@pytest.fixture
def mock_session():
    """Creates a mock AsyncSession object.

    Returns:
        AsyncMock: A mock instance of AsyncSession.
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contacts_repository(mock_session):
    """Creates a ContactsRepository instance with a mock session.

    Args:
        mock_session (AsyncMock): The mock database session.

    Returns:
        ContactsRepository: An instance of ContactsRepository.
    """
    return ContactsRepository(mock_session)


@pytest.fixture
def mock_user():
    """Creates a mock User object.

    Returns:
        User: A mock User instance.
    """
    return User(id=1, username="test_user", role="ADMIN")


@pytest.fixture
def mock_contact(mock_user):
    """Creates a mock Contact object.

    Args:
        mock_user (User): The mock user associated with the contact.

    Returns:
        Contact: A mock Contact instance.
    """
    return Contact(
        id=2,
        first_name="John",
        last_name="Doe",
        email="john_doe@example.com",
        phone="987654321",
        birthday=date(1990, 5, 15),
        user=mock_user,
    )


@pytest.fixture
def mock_contacts_list(mock_user):
    """Creates a list of mock Contact objects.

    Args:
        mock_user (User): The mock user associated with the contacts.

    Returns:
        list: A list of mock Contact instances.
    """
    return [
        Contact(
            id=1,
            first_name="Alice",
            last_name="Johnson",
            email="alice_johnson@example.com",
            phone="123456789",
            birthday=date(1992, 3, 14),
            user=mock_user,
        ),
        Contact(
            id=2,
            first_name="Bob",
            last_name="Brown",
            email="bob_brown@example.com",
            phone="987654321",
            birthday=date(1988, 7, 19),
            user=mock_user,
        ),
        Contact(
            id=3,
            first_name="Charlie",
            last_name="Davis",
            email="charlie_davis@example.com",
            phone="456789123",
            birthday=date(1995, 11, 30),
            user=mock_user,
        ),
    ]


@pytest.mark.asyncio
async def test_get_contacts(
    contacts_repository, mock_session, mock_user, mock_contacts_list
):
    """Tests the get_contacts method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contacts_list (list): A list of mock contacts.
    """
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_contacts(mock_user, 10, 0)

    assert result == mock_contacts_list
    assert len(result) == len(mock_contacts_list)
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_contact_by_id(
    contacts_repository, mock_session, mock_user, mock_contact
):
    """Tests the get_contact_by_id method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contact (Contact): The mock contact.
    """
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_contact_by_id(mock_user, mock_contact.id)

    assert result == mock_contact
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_contact(contacts_repository, mock_session, mock_user):
    """Tests the create_contact method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
    """
    contact_id = 4
    contact_data = BaseContact(
        first_name="testname",
        last_name="testsurname",
        email="test@mail.com",
        phone="123456789",
        birthday=date(1990, 5, 15),
    )

    mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", contact_id)

    result = await contacts_repository.create_contact(mock_user, contact_data)

    assert isinstance(result, Contact)
    assert result.id == contact_id
    assert result.first_name == contact_data.first_name
    assert result.last_name == contact_data.last_name
    assert result.email == contact_data.email
    assert result.phone == contact_data.phone
    assert result.birthday == contact_data.birthday
    assert result.user == mock_user
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact(
    contacts_repository, mock_session, mock_user, mock_contact
):
    """Tests the update_contact method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contact (Contact): The mock contact.
    """
    update_data = UpdateContact(first_name="UpdatedName")
    contacts_repository.get_contact_by_id = AsyncMock(return_value=mock_contact)

    result = await contacts_repository.update_contact(
        mock_user, mock_contact.id, update_data
    )

    assert result.first_name == update_data.first_name
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_contact(
    contacts_repository, mock_session, mock_user, mock_contact
):
    """Tests the remove_contact method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contact (Contact): The mock contact.
    """
    contacts_repository.get_contact_by_id = AsyncMock(return_value=mock_contact)

    result = await contacts_repository.remove_contact(mock_user, mock_contact.id)

    assert result == mock_contact
    mock_session.delete.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_contacts(
    contacts_repository, mock_session, mock_user, mock_contacts_list
):
    """Tests the search_contacts method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contacts_list (list): A list of mock contacts.
    """
    query = ["Alice", "alice_johnson@example.com"]
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list[0]
    mock_session.execute.return_value = mock_result

    result1 = await contacts_repository.search_contacts(mock_user, query[0])
    result2 = await contacts_repository.search_contacts(mock_user, query[1])

    assert result1 == mock_contacts_list[0]
    assert result2 == mock_contacts_list[0]

    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(
    contacts_repository, mock_session, mock_user, mock_contacts_list
):
    """Tests the get_upcoming_birthdays method of ContactsRepository.

    Args:
        contacts_repository (ContactsRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        mock_user (User): The mock user.
        mock_contacts_list (list): A list of mock contacts.
    """
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = mock_contacts_list[2]
    mock_session.execute.return_value = mock_result

    result = await contacts_repository.get_upcoming_birthdays(
        days_ahead=7, user=mock_user
    )

    assert result == mock_contacts_list[2]
    mock_session.execute.assert_awaited_once()
