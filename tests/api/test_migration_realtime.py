# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `asyncio` because this module uses that dependency.
import asyncio

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `datetime` for this module.
from datetime import timedelta

# Imports `pytest` because this module uses that dependency.
import pytest

# Imports the required names from `mastermind_api.models` for this module.
from mastermind_api.models import FeatureFlag, Profile

# Imports the required names from `mastermind_api.realtime` for this module.
from mastermind_api.realtime import InMemoryBroker

# Imports the required names from `mastermind_api.schemas` for this module.
from mastermind_api.schemas import RoomClientMessage

# Imports the required names from `mastermind_api.services` for this module.
from mastermind_api.services import utcnow

# Imports the required names from `pydantic` for this module.
from pydantic import ValidationError

# Imports the required names from `.conftest` for this module.
from .conftest import APIContext


# Defines this callable to implement the operation described by its name.
async def test_mongodb_indexes_and_seed_documents_are_initialized(api: APIContext) -> None:
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Performs this required operation before the surrounding flow continues.
        assert 'ICT-SBA' in await session.database.list_collection_names()
        # Stores `flag` because later steps depend on this value.
        flag = await session.get(FeatureFlag, 'daily')
        # Performs this required operation before the surrounding flow continues.
        assert flag is not None and flag.enabled is True
        # Stores `indexes` because later steps depend on this value.
        indexes = await session.database['auth_sessions'].index_information()
        # Performs this required operation before the surrounding flow continues.
        assert any(index.get('unique') for index in indexes.values())
        # Performs this required operation before the surrounding flow continues.
        assert any(index.get('expireAfterSeconds') == 0 for index in indexes.values())


# Defines this callable to implement the operation described by its name.
async def test_mongodb_transaction_rolls_back_failed_unit_of_work(api: APIContext) -> None:
    # Stores `user_id` because later steps depend on this value.
    user_id = uuid.uuid4()
    # Scopes this resource so acquisition and cleanup remain paired.
    with pytest.raises(RuntimeError):
        # Scopes this resource so acquisition and cleanup remain paired.
        async with api.sessions() as session:
            # Supplies this required nested value.
            session.add(Profile(id=user_id, display_name='Temporary'))
            # Performs this required operation before the surrounding flow continues.
            await session.flush()
            # Raises this error so invalid state cannot continue silently.
            raise RuntimeError('force rollback')
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Performs this required operation before the surrounding flow continues.
        assert await session.get(Profile, user_id) is None


# Defines this callable to implement the operation described by its name.
async def test_in_memory_broker_fans_out_and_unsubscribes() -> None:
    # Stores `broker` because later steps depend on this value.
    broker = InMemoryBroker()
    # Scopes this resource so acquisition and cleanup remain paired.
    async with broker.subscribe('room') as first, broker.subscribe('room') as second:
        # Stores `event` because later steps depend on this value.
        event = {'version': 1, 'sequence': 1, 'type': 'presence', 'payload': {}}
        # Performs this required operation before the surrounding flow continues.
        await broker.publish('room', event)
        # Performs this required operation before the surrounding flow continues.
        assert await asyncio.wait_for(anext(first), timeout=1) == event
        # Performs this required operation before the surrounding flow continues.
        assert await asyncio.wait_for(anext(second), timeout=1) == event
    # Performs this required operation before the surrounding flow continues.
    await broker.close()


# Defines this callable to implement the operation described by its name.
def test_realtime_envelopes_are_versioned_and_reject_unknown_versions() -> None:
    # Stores `message` because later steps depend on this value.
    message = RoomClientMessage(
        # Stores `version` because later steps depend on this value.
        version=1,
        # Stores `type` because later steps depend on this value.
        type='guess',
        # Stores `guess` because later steps depend on this value.
        guess=['R', 'B', 'G', 'Y'],
        # Stores `idempotency_key` because later steps depend on this value.
        idempotency_key='realtime-test-001',
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert message.version == 1
    # Scopes this resource so acquisition and cleanup remain paired.
    with pytest.raises(ValidationError):
        # Supplies this required nested value.
        RoomClientMessage.model_validate({'version': 2, 'type': 'heartbeat'})


# Defines this callable to implement the operation described by its name.
def test_utcnow_is_timezone_aware() -> None:
    # Stores `now` because later steps depend on this value.
    now = utcnow()
    # Performs this required operation before the surrounding flow continues.
    assert now.tzinfo is not None
    # Performs this required operation before the surrounding flow continues.
    assert now + timedelta(seconds=1) > now
