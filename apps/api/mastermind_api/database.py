# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `asyncio` because this module uses that dependency.
import asyncio

# Imports the required names from `collections.abc` for this module.
from collections.abc import AsyncIterator

# Imports the required names from `contextlib` for this module.
from contextlib import suppress

# Imports the required names from `dataclasses` for this module.
from dataclasses import fields, is_dataclass

# Imports the required names from `datetime` for this module.
from datetime import UTC, date, datetime

# Imports the required names from `typing` for this module.
from typing import Any, TypeVar, cast

# Imports the required names from `bson.binary` for this module.
from bson.binary import UuidRepresentation

# Imports the required names from `bson.codec_options` for this module.
from bson.codec_options import CodecOptions

# Imports the required names from `pymongo` for this module.
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, IndexModel

# Imports the required names from `pymongo.asynchronous.client_session` for this module.
from pymongo.asynchronous.client_session import AsyncClientSession

# Imports the required names from `pymongo.asynchronous.collection` for this module.
from pymongo.asynchronous.collection import AsyncCollection

# Imports the required names from `pymongo.asynchronous.database` for this module.
from pymongo.asynchronous.database import AsyncDatabase

# Imports the required names from `pymongo.errors` for this module.
from pymongo.errors import CollectionInvalid

# Imports the required names from `.config` for this module.
from .config import Settings, get_settings

# Imports the required names from `.models` for this module.
from .models import (
    # Supplies this required nested value.
    Achievement,
    # Supplies this required nested value.
    Document,
    # Supplies this required nested value.
    FeatureFlag,
    # Supplies this required nested value.
    GameAttempt,
    # Supplies this required nested value.
    GameSession,
    # Supplies this required nested value.
    TimestampedDocument,
    # Supplies this required nested value.
    utcnow,
    # Closes the multiline declaration, call, or collection opened above.
)

# Stores `TDocument` because later steps depend on this value.
TDocument = TypeVar("TDocument", bound=Document)

# Stores `_client` because later steps depend on this value.
_client: AsyncMongoClient[dict[str, Any]] | None = None
# Stores `_database` because later steps depend on this value.
_database: AsyncDatabase[dict[str, Any]] | None = None
# Stores `_settings_override` because later steps depend on this value.
_settings_override: Settings | None = None


# Defines this callable to implement the operation described by its name.
def configure_database(settings: Settings) -> None:
    # Supplies this required nested value.
    global _settings_override
    # Guards the nested operation so it runs only when this condition is satisfied.
    if _client is not None:
        # Raises this error so invalid state cannot continue silently.
        raise RuntimeError("Database settings cannot change while a MongoDB client is active.")
    # Stores `_settings_override` because later steps depend on this value.
    _settings_override = settings


# Defines this callable to implement the operation described by its name.
def _encode(value: Any) -> Any:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if isinstance(value, date) and not isinstance(value, datetime):
        # Returns the computed result and ends the current callable.
        return value.isoformat()
    # Guards the nested operation so it runs only when this condition is satisfied.
    if is_dataclass(value):
        # Returns the computed result and ends the current callable.
        return {item.name: _encode(getattr(value, item.name)) for item in fields(value)}
    # Guards the nested operation so it runs only when this condition is satisfied.
    if isinstance(value, dict):
        # Returns the computed result and ends the current callable.
        return {key: _encode(item) for key, item in value.items()}
    # Guards the nested operation so it runs only when this condition is satisfied.
    if isinstance(value, list | tuple):
        # Returns the computed result and ends the current callable.
        return [_encode(item) for item in value]
    # Returns the computed result and ends the current callable.
    return value


# Defines this callable to implement the operation described by its name.
def _encode_filter(value: Any) -> Any:
    # Guards the nested operation so it runs only when this condition is satisfied.
    if isinstance(value, dict):
        # Returns the computed result and ends the current callable.
        return {key: _encode_filter(item) for key, item in value.items()}
    # Guards the nested operation so it runs only when this condition is satisfied.
    if isinstance(value, list | tuple):
        # Returns the computed result and ends the current callable.
        return [_encode_filter(item) for item in value]
    # Returns the computed result and ends the current callable.
    return _encode(value)


# Defines this callable to implement the operation described by its name.
def document_to_bson(instance: Document) -> dict[str, Any]:
    # Stores `primary_key` because later steps depend on this value.
    primary_key = instance.primary_key
    # Stores `document` because later steps depend on this value.
    document = {
        # Supplies this required nested value.
        item.name: _encode(getattr(instance, item.name))
        # Iterates over these values so each item receives the same processing.
        for item in fields(instance)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if item.name != primary_key
        # Closes the multiline declaration, call, or collection opened above.
    }
    # Supplies this required nested value.
    document["_id"] = _encode(getattr(instance, primary_key))
    # Returns the computed result and ends the current callable.
    return document


# Defines this callable to implement the operation described by its name.
def document_from_bson[T: Document](model: type[T], raw: dict[str, Any]) -> T:
    # Stores `values` because later steps depend on this value.
    values = dict(raw)
    # Supplies this required nested value.
    values[model.primary_key] = values.pop("_id")
    # Guards the nested operation so it runs only when this condition is satisfied.
    if model is GameSession:
        # Supplies this required nested value.
        values["attempts"] = [GameAttempt(**attempt) for attempt in values.get("attempts", [])]
    # Guards the nested operation so it runs only when this condition is satisfied.
    if "challenge_date" in values and isinstance(values["challenge_date"], str):
        # Supplies this required nested value.
        values["challenge_date"] = date.fromisoformat(values["challenge_date"])
    # Returns the computed result and ends the current callable.
    return model(**values)


# Defines this callable to implement the operation described by its name.
def get_client() -> AsyncMongoClient[dict[str, Any]]:
    # Supplies this required nested value.
    global _client
    # Guards the nested operation so it runs only when this condition is satisfied.
    if _client is None:
        # Stores `settings` because later steps depend on this value.
        settings = _settings_override or get_settings()
        # Stores `_client` because later steps depend on this value.
        _client = AsyncMongoClient(
            # Supplies this required nested value.
            settings.mongodb_url,
            # Stores `appname` because later steps depend on this value.
            appname="cipherboard-api",
            # Stores `retryWrites` because later steps depend on this value.
            retryWrites=True,
            # Stores `uuidRepresentation` because later steps depend on this value.
            uuidRepresentation="standard",
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Returns the computed result and ends the current callable.
    return _client


# Defines this callable to implement the operation described by its name.
def get_database() -> AsyncDatabase[dict[str, Any]]:
    # Supplies this required nested value.
    global _database
    # Guards the nested operation so it runs only when this condition is satisfied.
    if _database is None:
        # Stores `settings` because later steps depend on this value.
        settings = _settings_override or get_settings()
        # Stores `codec_options` because later steps depend on this value.
        codec_options: CodecOptions[dict[str, Any]] = CodecOptions(
            # Stores `tz_aware` because later steps depend on this value.
            tz_aware=True,
            # Stores `tzinfo` because later steps depend on this value.
            tzinfo=UTC,
            # Stores `uuid_representation` because later steps depend on this value.
            uuid_representation=UuidRepresentation.STANDARD,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Stores `_database` because later steps depend on this value.
        _database = get_client().get_database(
            # Supplies this required nested value.
            settings.mongodb_database,
            codec_options=codec_options,
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Returns the computed result and ends the current callable.
    return _database


# Groups the state and behavior owned by `MongoSession`.
class MongoSession:
    # Defines this callable to implement the operation described by its name.
    def __init__(self) -> None:
        # Stores `self.database` because later steps depend on this value.
        self.database = get_database()
        # Stores `self._mongo_session` because later steps depend on this value.
        self._mongo_session: AsyncClientSession | None = None
        # Stores `self._tracked` because later steps depend on this value.
        self._tracked: dict[tuple[type[Document], Any], Document] = {}
        # Stores `self._snapshots` because later steps depend on this value.
        self._snapshots: dict[tuple[type[Document], Any], dict[str, Any]] = {}
        # Stores `self._new` because later steps depend on this value.
        self._new: set[tuple[type[Document], Any]] = set()
        # Stores `self._inserted` because later steps depend on this value.
        self._inserted: set[tuple[type[Document], Any]] = set()
        # Stores `self._deleted` because later steps depend on this value.
        self._deleted: set[tuple[type[Document], Any]] = set()

    # Defines this callable to implement the operation described by its name.
    async def __aenter__(self) -> MongoSession:
        # Stores `self._mongo_session` because later steps depend on this value.
        self._mongo_session = get_client().start_session()
        # Performs this required operation before the surrounding flow continues.
        await self._mongo_session.__aenter__()
        # Performs this required operation before the surrounding flow continues.
        await self._mongo_session.start_transaction()
        # Returns the computed result and ends the current callable.
        return self

    # Defines this callable to implement the operation described by its name.
    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self._mongo_session is None:
            # Returns the computed result and ends the current callable.
            return
        # Starts an operation whose expected failures are handled below.
        try:
            # Guards the nested operation so it runs only when this condition is satisfied.
            if self._mongo_session.in_transaction:
                # Guards the nested operation so it runs only when this condition is satisfied.
                if exc_type is None:
                    # Performs this required operation before the surrounding flow continues.
                    await self.flush()
                    # Performs this required operation before the surrounding flow continues.
                    await self._mongo_session.commit_transaction()
                # Provides the fallback path when the preceding conditions do not match.
                else:
                    # Performs this required operation before the surrounding flow continues.
                    await self._mongo_session.abort_transaction()
        # Ensures this cleanup runs whether the protected operation succeeds or fails.
        finally:
            # Performs this required operation before the surrounding flow continues.
            await self._mongo_session.__aexit__(exc_type, exc, traceback)
            # Stores `self._mongo_session` because later steps depend on this value.
            self._mongo_session = None

    # Defines this callable to implement the operation described by its name.
    def collection(self, model: type[TDocument]) -> AsyncCollection[dict[str, Any]]:
        # Returns the computed result and ends the current callable.
        return self.database[model.collection]

    # Defines this callable to implement the operation described by its name.
    def _key(self, model: type[TDocument], primary_value: Any) -> tuple[type[Document], Any]:
        # Returns the computed result and ends the current callable.
        return cast(tuple[type[Document], Any], (model, primary_value))

    # Defines this callable to implement the operation described by its name.
    def _track(self, instance: TDocument, *, new: bool = False) -> TDocument:
        # Stores `key` because later steps depend on this value.
        key = self._key(type(instance), getattr(instance, instance.primary_key))
        # Stores `current` because later steps depend on this value.
        current = self._tracked.get(key)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if current is not None:
            # Returns the computed result and ends the current callable.
            return cast(TDocument, current)
        # Supplies this required nested value.
        self._tracked[key] = instance
        # Supplies this required nested value.
        self._snapshots[key] = document_to_bson(instance)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if new:
            # Supplies this required nested value.
            self._new.add(key)
        # Returns the computed result and ends the current callable.
        return instance

    # Defines this callable to implement the operation described by its name.
    async def get(self, model: type[TDocument], primary_value: Any) -> TDocument | None:
        # Stores `key` because later steps depend on this value.
        key = self._key(model, primary_value)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if key in self._deleted:
            # Returns the computed result and ends the current callable.
            return None
        # Guards the nested operation so it runs only when this condition is satisfied.
        if key in self._tracked:
            # Returns the computed result and ends the current callable.
            return cast(TDocument, self._tracked[key])
        # Stores `raw` because later steps depend on this value.
        raw = await self.collection(model).find_one(
            # Supplies this required nested value.
            {"_id": _encode(primary_value)},
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Returns the computed result and ends the current callable.
        return self._track(document_from_bson(model, raw)) if raw else None

    # Defines this callable to implement the operation described by its name.
    async def find_one(
        # Supplies this required nested value.
        self,
        # Declares this typed field so the surrounding contract is explicit.
        model: type[TDocument],
        # Declares this typed field so the surrounding contract is explicit.
        filter: dict[str, Any],
        # Supplies this required nested value.
        *,
        # Stores `sort` because later steps depend on this value.
        sort: list[tuple[str, int]] | None = None,
        # Closes the multiline declaration, call, or collection opened above.
    ) -> TDocument | None:
        # Stores `raw` because later steps depend on this value.
        raw = await self.collection(model).find_one(
            # Supplies this required nested value.
            _encode_filter(filter),
            sort=sort,
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Returns the computed result and ends the current callable.
        return self._track(document_from_bson(model, raw)) if raw else None

    # Defines this callable to implement the operation described by its name.
    async def find_many(
        # Supplies this required nested value.
        self,
        # Declares this typed field so the surrounding contract is explicit.
        model: type[TDocument],
        # Stores `filter` because later steps depend on this value.
        filter: dict[str, Any] | None = None,
        # Supplies this required nested value.
        *,
        # Stores `sort` because later steps depend on this value.
        sort: list[tuple[str, int]] | None = None,
        # Stores `skip` because later steps depend on this value.
        skip: int = 0,
        # Stores `limit` because later steps depend on this value.
        limit: int = 0,
        # Closes the multiline declaration, call, or collection opened above.
    ) -> list[TDocument]:
        # Stores `cursor` because later steps depend on this value.
        cursor = self.collection(model).find(
            # Supplies this required nested value.
            _encode_filter(filter or {}),
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Guards the nested operation so it runs only when this condition is satisfied.
        if sort:
            # Stores `cursor` because later steps depend on this value.
            cursor = cursor.sort(sort)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if skip:
            # Stores `cursor` because later steps depend on this value.
            cursor = cursor.skip(skip)
        # Guards the nested operation so it runs only when this condition is satisfied.
        if limit:
            # Stores `cursor` because later steps depend on this value.
            cursor = cursor.limit(limit)
        # Returns the computed result and ends the current callable.
        return [self._track(document_from_bson(model, raw)) for raw in await cursor.to_list()]

    # Defines this callable to implement the operation described by its name.
    async def count(self, model: type[TDocument], filter: dict[str, Any] | None = None) -> int:
        # Returns the computed result and ends the current callable.
        return await self.collection(model).count_documents(
            # Supplies this required nested value.
            _encode_filter(filter or {}),
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )

    # Defines this callable to implement the operation described by its name.
    async def aggregate(
        # Supplies this required nested value.
        self,
        model: type[TDocument],
        pipeline: list[dict[str, Any]],
        # Closes the multiline declaration, call, or collection opened above.
    ) -> list[dict[str, Any]]:
        # Stores `cursor` because later steps depend on this value.
        cursor = await self.collection(model).aggregate(
            # Supplies this required nested value.
            _encode_filter(pipeline),
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Returns the computed result and ends the current callable.
        return await cursor.to_list()

    # Defines this callable to implement the operation described by its name.
    def add(self, instance: TDocument) -> None:
        # Supplies this required nested value.
        self._track(instance, new=True)

    # Defines this callable to implement the operation described by its name.
    def add_all(self, instances: list[TDocument]) -> None:
        # Iterates over these values so each item receives the same processing.
        for instance in instances:
            # Supplies this required nested value.
            self.add(instance)

    # Defines this callable to implement the operation described by its name.
    async def delete(self, instance: TDocument) -> None:
        # Stores `key` because later steps depend on this value.
        key = self._key(type(instance), getattr(instance, instance.primary_key))
        # Supplies this required nested value.
        self._deleted.add(key)

    # Defines this callable to implement the operation described by its name.
    async def update_many(
        # Supplies this required nested value.
        self,
        model: type[TDocument],
        filter: dict[str, Any],
        update: dict[str, Any],
        # Closes the multiline declaration, call, or collection opened above.
    ) -> int:
        # Stores `result` because later steps depend on this value.
        result = await self.collection(model).update_many(
            # Supplies this required nested value.
            _encode_filter(filter),
            _encode_filter(update),
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Returns the computed result and ends the current callable.
        return result.modified_count

    # Defines this callable to implement the operation described by its name.
    async def upsert_one(
        # Supplies this required nested value.
        self,
        # Declares this typed field so the surrounding contract is explicit.
        model: type[TDocument],
        # Declares this typed field so the surrounding contract is explicit.
        filter: dict[str, Any],
        # Declares this typed field so the surrounding contract is explicit.
        update: dict[str, Any],
        # Closes the multiline declaration, call, or collection opened above.
    ) -> None:
        # Performs this required operation before the surrounding flow continues.
        await self.collection(model).update_one(
            # Supplies this required nested value.
            _encode_filter(filter),
            # Supplies this required nested value.
            _encode_filter(update),
            # Stores `upsert` because later steps depend on this value.
            upsert=True,
            # Stores `session` because later steps depend on this value.
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )

    # Defines this callable to implement the operation described by its name.
    async def delete_many(self, model: type[TDocument], filter: dict[str, Any]) -> int:
        # Stores `result` because later steps depend on this value.
        result = await self.collection(model).delete_many(
            # Supplies this required nested value.
            _encode_filter(filter),
            session=self._mongo_session,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Returns the computed result and ends the current callable.
        return result.deleted_count

    # Defines this callable to implement the operation described by its name.
    async def flush(self) -> None:
        # Iterates over these values so each item receives the same processing.
        for key in list(self._deleted):
            # Supplies this required nested value.
            model, primary_value = key
            # Performs this required operation before the surrounding flow continues.
            await self.collection(model).delete_one(
                # Supplies this required nested value.
                {"_id": _encode(primary_value)},
                session=self._mongo_session,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Supplies this required nested value.
            self._tracked.pop(key, None)
            # Supplies this required nested value.
            self._snapshots.pop(key, None)
            # Supplies this required nested value.
            self._new.discard(key)
            # Supplies this required nested value.
            self._inserted.discard(key)
        # Supplies this required nested value.
        self._deleted.clear()

        # Iterates over these values so each item receives the same processing.
        for key, instance in list(self._tracked.items()):
            # Guards the nested operation so it runs only when this condition is satisfied.
            if isinstance(instance, TimestampedDocument):
                # Stores `current` because later steps depend on this value.
                current = document_to_bson(instance)
                # Guards the nested operation so it runs only when this condition is satisfied.
                if key in self._new or current != self._snapshots.get(key):
                    # Stores `instance.updated_at` because later steps depend on this value.
                    instance.updated_at = utcnow()
            # Stores `document` because later steps depend on this value.
            document = document_to_bson(instance)
            # Stores `collection` because later steps depend on this value.
            collection = self.collection(type(instance))
            # Guards the nested operation so it runs only when this condition is satisfied.
            if key in self._new and key not in self._inserted:
                # Performs this required operation before the surrounding flow continues.
                await collection.insert_one(document, session=self._mongo_session)
                # Supplies this required nested value.
                self._inserted.add(key)
            # Handles this alternative only when the earlier conditions did not match.
            elif document != self._snapshots.get(key):
                # Performs this required operation before the surrounding flow continues.
                await collection.replace_one(
                    # Supplies this required nested value.
                    {"_id": document["_id"]},
                    document,
                    session=self._mongo_session,
                    # Closes the multiline declaration, call, or collection opened above.
                )
            # Supplies this required nested value.
            self._snapshots[key] = document

    # Defines this callable to implement the operation described by its name.
    async def commit(self) -> None:
        # Performs this required operation before the surrounding flow continues.
        await self.flush()
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self._mongo_session is not None and self._mongo_session.in_transaction:
            # Performs this required operation before the surrounding flow continues.
            await self._mongo_session.commit_transaction()
            # Performs this required operation before the surrounding flow continues.
            await self._mongo_session.start_transaction()
        # Supplies this required nested value.
        self._new.clear()
        # Supplies this required nested value.
        self._inserted.clear()

    # Defines this callable to implement the operation described by its name.
    async def rollback(self) -> None:
        # Guards the nested operation so it runs only when this condition is satisfied.
        if self._mongo_session is not None and self._mongo_session.in_transaction:
            # Performs this required operation before the surrounding flow continues.
            await self._mongo_session.abort_transaction()
            # Performs this required operation before the surrounding flow continues.
            await self._mongo_session.start_transaction()
        # Supplies this required nested value.
        self._tracked.clear()
        # Supplies this required nested value.
        self._snapshots.clear()
        # Supplies this required nested value.
        self._new.clear()
        # Supplies this required nested value.
        self._inserted.clear()
        # Supplies this required nested value.
        self._deleted.clear()


# Groups the state and behavior owned by `MongoSessionFactory`.
class MongoSessionFactory:
    # Defines this callable to implement the operation described by its name.
    def __call__(self) -> MongoSession:
        # Returns the computed result and ends the current callable.
        return MongoSession()


# Stores `SessionFactory` because later steps depend on this value.
SessionFactory = MongoSessionFactory()


# Defines this callable to implement the operation described by its name.
async def get_session() -> AsyncIterator[MongoSession]:
    # Scopes this resource so acquisition and cleanup remain paired.
    async with SessionFactory() as session:
        # Supplies this required nested value.
        yield session


# Defines this callable to implement the operation described by its name.
async def initialize_database() -> None:
    # Stores `database` because later steps depend on this value.
    database = get_database()
    # Guards the nested operation so it runs only when this condition is satisfied.
    if "ICT-SBA" not in await database.list_collection_names():
        # Scopes this resource so acquisition and cleanup remain paired.
        with suppress(CollectionInvalid):
            # Performs this required operation before the surrounding flow continues.
            await database.create_collection("ICT-SBA")
    # Stores `index_sets` because later steps depend on this value.
    index_sets: dict[str, list[IndexModel]] = {
        # Supplies this literal value to the surrounding declaration or call.
        "profiles": [
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("normalized_display_name", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"normalized_display_name": {"$type": "string"}},
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "auth_users": [
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("normalized_email", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"normalized_email": {"$type": "string"}},
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "auth_sessions": [
            # Supplies this required nested value.
            IndexModel([("refresh_token_hash", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)]),
            # Supplies this required nested value.
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "auth_email_tokens": [
            # Supplies this required nested value.
            IndexModel([("token_hash", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "daily_challenges": [
            # Supplies this required nested value.
            IndexModel([("public_id", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("challenge_date", ASCENDING), ("rule_set_version", ASCENDING)],
                unique=True,
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "friend_challenges": [
            # Supplies this required nested value.
            IndexModel([("share_code_hash", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("creator_id", ASCENDING), ("created_at", DESCENDING)]),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("creator_id", ASCENDING), ("creation_idempotency_key", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"creation_idempotency_key": {"$type": "string"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "multiplayer_rooms": [
            # Supplies this required nested value.
            IndexModel([("room_code_hash", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("status", ASCENDING), ("expires_at", ASCENDING)]),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("owner_id", ASCENDING), ("creation_idempotency_key", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"creation_idempotency_key": {"$type": "string"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "game_sessions": [
            # Supplies this required nested value.
            IndexModel([("public_id", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)]),
            # Supplies this required nested value.
            IndexModel([("status", ASCENDING), ("expires_at", ASCENDING)]),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("owner_id", ASCENDING), ("creation_idempotency_key", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"creation_idempotency_key": {"$type": "string"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("owner_id", ASCENDING), ("daily_challenge_id", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"daily_challenge_id": {"$type": "binData"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("owner_id", ASCENDING), ("friend_challenge_id", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"friend_challenge_id": {"$type": "binData"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [("owner_id", ASCENDING), ("room_id", ASCENDING)],
                # Stores `unique` because later steps depend on this value.
                unique=True,
                # Stores `partialFilterExpression` because later steps depend on this value.
                partialFilterExpression={"room_id": {"$type": "binData"}},
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "multiplayer_members": [
            # Supplies this required nested value.
            IndexModel([("room_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "multiplayer_events": [
            # Supplies this required nested value.
            IndexModel([("room_id", ASCENDING), ("sequence", ASCENDING)], unique=True)
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "leaderboard_entries": [
            # Supplies this required nested value.
            IndexModel([("game_id", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel(
                # Supplies this required nested value.
                [
                    # Supplies this required nested value.
                    ("category", ASCENDING),
                    # Supplies this required nested value.
                    ("score", DESCENDING),
                    # Supplies this required nested value.
                    ("attempts_used", ASCENDING),
                    # Supplies this required nested value.
                    ("elapsed_seconds", ASCENDING),
                    # Closes the multiline declaration, call, or collection opened above.
                ]
                # Closes the multiline declaration, call, or collection opened above.
            ),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "user_achievements": [
            # Supplies this required nested value.
            IndexModel([("user_id", ASCENDING), ("achievement_key", ASCENDING)], unique=True)
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Supplies this literal value to the surrounding declaration or call.
        "account_deletion_requests": [IndexModel([("user_id", ASCENDING)], unique=True)],
        # Supplies this literal value to the surrounding declaration or call.
        "product_events": [
            # Supplies this required nested value.
            IndexModel([("client_event_id", ASCENDING)], unique=True),
            # Supplies this required nested value.
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Closes the multiline declaration, call, or collection opened above.
    }
    # Iterates over these values so each item receives the same processing.
    for collection_name, indexes in index_sets.items():
        # Performs this required operation before the surrounding flow continues.
        await database[collection_name].create_indexes(indexes)

    # Stores `achievements` because later steps depend on this value.
    achievements = (
        # Supplies this required nested value.
        ("first_break", "First Break", "Win your first game."),
        # Supplies this required nested value.
        ("one_shot", "One Shot", "Solve a code on your first attempt."),
        # Supplies this required nested value.
        ("no_waste", "No Waste", "Win without an invalid submission."),
        # Supplies this required nested value.
        ("daily_debut", "Daily Debut", "Complete your first daily challenge."),
        # Supplies this required nested value.
        ("logic_week", "Logic Week", "Complete seven daily challenges."),
        # Supplies this required nested value.
        ("hard_mode", "Hard Mode", "Win an official Hard game."),
        # Supplies this required nested value.
        ("expert_breaker", "Expert Breaker", "Win an official Expert game."),
        # Supplies this required nested value.
        ("challenger", "Challenger", "Complete a friend challenge."),
        # Supplies this required nested value.
        ("duelist", "Duelist", "Win a private real-time duel."),
        # Supplies this required nested value.
        ("comeback", "Comeback", "Win a duel after trailing your opponent."),
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Iterates over these values so each item receives the same processing.
    for key, name, description in achievements:
        # Performs this required operation before the surrounding flow continues.
        await database[Achievement.collection].update_one(
            # Supplies this required nested value.
            {"_id": key},
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "$setOnInsert": document_to_bson(
                    # Supplies this required nested value.
                    Achievement(key=key, name=name, description=description)
                    # Closes the multiline declaration, call, or collection opened above.
                )
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Stores `upsert` because later steps depend on this value.
            upsert=True,
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Stores `flags` because later steps depend on this value.
    flags = {
        # Supplies this literal value to the surrounding declaration or call.
        "daily": "Official daily challenge",
        # Supplies this literal value to the surrounding declaration or call.
        "leaderboards": "Public leaderboards",
        # Supplies this literal value to the surrounding declaration or call.
        "friend_challenges": "Private asynchronous challenges",
        # Supplies this literal value to the surrounding declaration or call.
        "multiplayer": "Private real-time duels",
        # Supplies this literal value to the surrounding declaration or call.
        "achievements": "Achievement awarding",
        # Supplies this literal value to the surrounding declaration or call.
        "account_registration": "Registered account upgrades",
        # Supplies this literal value to the surrounding declaration or call.
        "analytics": "Privacy-conscious first-party analytics",
        # Closes the multiline declaration, call, or collection opened above.
    }
    # Iterates over these values so each item receives the same processing.
    for key, description in flags.items():
        # Performs this required operation before the surrounding flow continues.
        await database[FeatureFlag.collection].update_one(
            # Supplies this required nested value.
            {"_id": key},
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "$setOnInsert": document_to_bson(
                    # Supplies this required nested value.
                    FeatureFlag(key=key, enabled=True, description=description)
                    # Closes the multiline declaration, call, or collection opened above.
                )
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Stores `upsert` because later steps depend on this value.
            upsert=True,
            # Closes the multiline declaration, call, or collection opened above.
        )


# Defines this callable to implement the operation described by its name.
async def close_database() -> None:
    # Supplies this required nested value.
    global _client, _database
    # Guards the nested operation so it runs only when this condition is satisfied.
    if _client is not None:
        # Performs this required operation before the surrounding flow continues.
        await _client.close()
    # Stores `_client` because later steps depend on this value.
    _client = None
    # Stores `_database` because later steps depend on this value.
    _database = None


# Defines this callable to implement the operation described by its name.
async def database_ready() -> bool:
    # Starts an operation whose expected failures are handled below.
    try:
        # Performs this required operation before the surrounding flow continues.
        await get_database().command("ping")
    # Converts this expected failure into the controlled behavior below.
    except Exception:
        # Returns the computed result and ends the current callable.
        return False
    # Returns the computed result and ends the current callable.
    return True


# Defines this callable to implement the operation described by its name.
async def _initialize_and_close() -> None:
    # Starts an operation whose expected failures are handled below.
    try:
        # Performs this required operation before the surrounding flow continues.
        await initialize_database()
    # Ensures this cleanup runs whether the protected operation succeeds or fails.
    finally:
        # Performs this required operation before the surrounding flow continues.
        await close_database()


# Defines this callable to implement the operation described by its name.
def main() -> None:
    # Supplies this required nested value.
    asyncio.run(_initialize_and_close())


# Stores `__all__` because later steps depend on this value.
__all__ = [
    # Supplies this literal value to the surrounding declaration or call.
    "ASCENDING",
    # Supplies this literal value to the surrounding declaration or call.
    "DESCENDING",
    # Supplies this literal value to the surrounding declaration or call.
    "MongoSession",
    # Supplies this literal value to the surrounding declaration or call.
    "SessionFactory",
    # Supplies this literal value to the surrounding declaration or call.
    "close_database",
    # Supplies this literal value to the surrounding declaration or call.
    "configure_database",
    # Supplies this literal value to the surrounding declaration or call.
    "database_ready",
    # Supplies this literal value to the surrounding declaration or call.
    "get_database",
    # Supplies this literal value to the surrounding declaration or call.
    "get_session",
    # Supplies this literal value to the surrounding declaration or call.
    "initialize_database",
    # Closes the multiline declaration, call, or collection opened above.
]
