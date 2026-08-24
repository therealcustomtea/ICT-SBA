# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `dataclasses` for this module.
from dataclasses import dataclass, field

# Imports the required names from `datetime` for this module.
from datetime import UTC, date, datetime

# Imports the required names from `typing` for this module.
from typing import Any, ClassVar


# Defines this callable to implement the operation described by its name.
def utcnow() -> datetime:
    # Returns the computed result and ends the current callable.
    return datetime.now(UTC)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `Document`.
class Document:
    # Declares this typed field so the surrounding contract is explicit.
    collection: ClassVar[str]
    # Stores `primary_key` because later steps depend on this value.
    primary_key: ClassVar[str] = 'id'


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `TimestampedDocument`.
class TimestampedDocument(Document):
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)
    # Stores `updated_at` because later steps depend on this value.
    updated_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `Profile`.
class Profile(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'profiles'
    # Declares this typed field so the surrounding contract is explicit.
    id: uuid.UUID
    # Stores `display_name` because later steps depend on this value.
    display_name: str | None = None
    # Stores `normalized_display_name` because later steps depend on this value.
    normalized_display_name: str | None = None
    # Stores `is_anonymous` because later steps depend on this value.
    is_anonymous: bool = True
    # Stores `public_leaderboards` because later steps depend on this value.
    public_leaderboards: bool = False
    # Stores `is_banned` because later steps depend on this value.
    is_banned: bool = False
    # Stores `deleted_at` because later steps depend on this value.
    deleted_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AuthUser`.
class AuthUser(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'auth_users'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Stores `email` because later steps depend on this value.
    email: str | None = None
    # Stores `normalized_email` because later steps depend on this value.
    normalized_email: str | None = None
    # Stores `is_anonymous` because later steps depend on this value.
    is_anonymous: bool = True
    # Stores `email_verified_at` because later steps depend on this value.
    email_verified_at: datetime | None = None
    # Stores `deleted_at` because later steps depend on this value.
    deleted_at: datetime | None = None
    # Stores `totp_secret_ciphertext` because later steps depend on this value.
    totp_secret_ciphertext: bytes | None = None
    # Stores `totp_secret_nonce` because later steps depend on this value.
    totp_secret_nonce: bytes | None = None
    # Stores `totp_secret_key_version` because later steps depend on this value.
    totp_secret_key_version: str | None = None
    # Stores `totp_enabled_at` because later steps depend on this value.
    totp_enabled_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AuthSession`.
class AuthSession(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'auth_sessions'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    refresh_token_hash: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Stores `previous_refresh_token_hash` because later steps depend on this value.
    previous_refresh_token_hash: str | None = None
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)
    # Stores `updated_at` because later steps depend on this value.
    updated_at: datetime = field(default_factory=utcnow)
    # Stores `authenticated_at` because later steps depend on this value.
    authenticated_at: datetime = field(default_factory=utcnow)
    # Stores `revoked_at` because later steps depend on this value.
    revoked_at: datetime | None = None
    # Stores `assurance_level` because later steps depend on this value.
    assurance_level: str = 'aal1'
    # Stores `last_ip_hash` because later steps depend on this value.
    last_ip_hash: str | None = None
    # Stores `user_agent_hash` because later steps depend on this value.
    user_agent_hash: str | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AuthEmailToken`.
class AuthEmailToken(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'auth_email_tokens'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    normalized_email: str
    # Declares this typed field so the surrounding contract is explicit.
    token_hash: str
    # Declares this typed field so the surrounding contract is explicit.
    purpose: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)
    # Stores `consumed_at` because later steps depend on this value.
    consumed_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `DailyChallenge`.
class DailyChallenge(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'daily_challenges'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    challenge_date: date
    # Declares this typed field so the surrounding contract is explicit.
    public_id: str
    # Declares this typed field so the surrounding contract is explicit.
    config: dict[str, Any]
    # Declares this typed field so the surrounding contract is explicit.
    derivation_version: str
    # Declares this typed field so the surrounding contract is explicit.
    derivation_key_version: str
    # Declares this typed field so the surrounding contract is explicit.
    rule_set_version: str


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `FriendChallenge`.
class FriendChallenge(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'friend_challenges'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    share_code_hash: str
    # Declares this typed field so the surrounding contract is explicit.
    creator_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    config: dict[str, Any]
    # Declares this typed field so the surrounding contract is explicit.
    encrypted_secret: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_nonce: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_key_version: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Stores `creation_idempotency_key` because later steps depend on this value.
    creation_idempotency_key: str | None = None
    # Stores `creation_request_fingerprint` because later steps depend on this value.
    creation_request_fingerprint: str | None = None
    # Stores `title` because later steps depend on this value.
    title: str | None = None
    # Stores `show_creator_name` because later steps depend on this value.
    show_creator_name: bool = True
    # Stores `revoked_at` because later steps depend on this value.
    revoked_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `MultiplayerRoom`.
class MultiplayerRoom(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'multiplayer_rooms'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    room_code_hash: str
    # Declares this typed field so the surrounding contract is explicit.
    owner_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    config: dict[str, Any]
    # Declares this typed field so the surrounding contract is explicit.
    encrypted_secret: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_nonce: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_key_version: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Stores `creation_idempotency_key` because later steps depend on this value.
    creation_idempotency_key: str | None = None
    # Stores `creation_request_fingerprint` because later steps depend on this value.
    creation_request_fingerprint: str | None = None
    # Stores `status` because later steps depend on this value.
    status: str = 'waiting'
    # Stores `winner_id` because later steps depend on this value.
    winner_id: uuid.UUID | None = None
    # Stores `winner_at` because later steps depend on this value.
    winner_at: datetime | None = None
    # Stores `tie_deadline` because later steps depend on this value.
    tie_deadline: datetime | None = None
    # Stores `is_tie` because later steps depend on this value.
    is_tie: bool = False
    # Stores `event_sequence` because later steps depend on this value.
    event_sequence: int = 0


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `GameAttempt`.
class GameAttempt:
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    game_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    attempt_number: int
    # Declares this typed field so the surrounding contract is explicit.
    guess: list[str]
    # Declares this typed field so the surrounding contract is explicit.
    black_pegs: int
    # Declares this typed field so the surrounding contract is explicit.
    white_pegs: int
    # Declares this typed field so the surrounding contract is explicit.
    idempotency_key: str
    # Declares this typed field so the surrounding contract is explicit.
    request_id: str
    # Stores `submitted_at` because later steps depend on this value.
    submitted_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `GameSession`.
class GameSession(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'game_sessions'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    public_id: str
    # Declares this typed field so the surrounding contract is explicit.
    owner_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    mode: str
    # Declares this typed field so the surrounding contract is explicit.
    config: dict[str, Any]
    # Declares this typed field so the surrounding contract is explicit.
    status: str
    # Declares this typed field so the surrounding contract is explicit.
    rule_set_version: str
    # Declares this typed field so the surrounding contract is explicit.
    scoring_version: str
    # Declares this typed field so the surrounding contract is explicit.
    encrypted_secret: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_nonce: bytes
    # Declares this typed field so the surrounding contract is explicit.
    secret_key_version: str
    # Declares this typed field so the surrounding contract is explicit.
    maximum_attempts: int
    # Declares this typed field so the surrounding contract is explicit.
    started_at: datetime
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Declares this typed field so the surrounding contract is explicit.
    ranked_eligibility: str
    # Stores `creation_idempotency_key` because later steps depend on this value.
    creation_idempotency_key: str | None = None
    # Stores `creation_request_fingerprint` because later steps depend on this value.
    creation_request_fingerprint: str | None = None
    # Stores `difficulty` because later steps depend on this value.
    difficulty: str | None = None
    # Stores `attempts_used` because later steps depend on this value.
    attempts_used: int = 0
    # Stores `completed_at` because later steps depend on this value.
    completed_at: datetime | None = None
    # Stores `elapsed_seconds` because later steps depend on this value.
    elapsed_seconds: int | None = None
    # Stores `final_score` because later steps depend on this value.
    final_score: int | None = None
    # Stores `score_breakdown` because later steps depend on this value.
    score_breakdown: dict[str, Any] | None = None
    # Stores `invalidation_reason` because later steps depend on this value.
    invalidation_reason: str | None = None
    # Stores `invalid_submission_count` because later steps depend on this value.
    invalid_submission_count: int = 0
    # Stores `daily_challenge_id` because later steps depend on this value.
    daily_challenge_id: uuid.UUID | None = None
    # Stores `friend_challenge_id` because later steps depend on this value.
    friend_challenge_id: uuid.UUID | None = None
    # Stores `room_id` because later steps depend on this value.
    room_id: uuid.UUID | None = None
    # Stores `attempts` because later steps depend on this value.
    attempts: list[GameAttempt] = field(default_factory=list)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `MultiplayerMember`.
class MultiplayerMember(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'multiplayer_members'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    room_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Stores `joined_at` because later steps depend on this value.
    joined_at: datetime = field(default_factory=utcnow)
    # Stores `last_seen_at` because later steps depend on this value.
    last_seen_at: datetime = field(default_factory=utcnow)
    # Stores `connected` because later steps depend on this value.
    connected: bool = False
    # Stores `ready` because later steps depend on this value.
    ready: bool = False
    # Stores `ready_at` because later steps depend on this value.
    ready_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `MultiplayerEvent`.
class MultiplayerEvent(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'multiplayer_events'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    room_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    sequence: int
    # Declares this typed field so the surrounding contract is explicit.
    event_type: str
    # Declares this typed field so the surrounding contract is explicit.
    payload: dict[str, Any]
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `LeaderboardEntry`.
class LeaderboardEntry(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'leaderboard_entries'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    game_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    category: str
    # Declares this typed field so the surrounding contract is explicit.
    score: int
    # Declares this typed field so the surrounding contract is explicit.
    attempts_used: int
    # Declares this typed field so the surrounding contract is explicit.
    elapsed_seconds: int
    # Declares this typed field so the surrounding contract is explicit.
    completed_at: datetime
    # Stores `review_status` because later steps depend on this value.
    review_status: str = 'approved'
    # Stores `invalidated_at` because later steps depend on this value.
    invalidated_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `Achievement`.
class Achievement(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'achievements'
    # Stores `primary_key` because later steps depend on this value.
    primary_key: ClassVar[str] = 'key'
    # Declares this typed field so the surrounding contract is explicit.
    key: str
    # Declares this typed field so the surrounding contract is explicit.
    name: str
    # Declares this typed field so the surrounding contract is explicit.
    description: str
    # Stores `version` because later steps depend on this value.
    version: int = 1


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `UserAchievement`.
class UserAchievement(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'user_achievements'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    achievement_key: str
    # Stores `awarded_at` because later steps depend on this value.
    awarded_at: datetime = field(default_factory=utcnow)
    # Stores `game_id` because later steps depend on this value.
    game_id: uuid.UUID | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `FeatureFlag`.
class FeatureFlag(TimestampedDocument):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'feature_flags'
    # Stores `primary_key` because later steps depend on this value.
    primary_key: ClassVar[str] = 'key'
    # Declares this typed field so the surrounding contract is explicit.
    key: str
    # Declares this typed field so the surrounding contract is explicit.
    enabled: bool
    # Stores `description` because later steps depend on this value.
    description: str | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `ModerationAction`.
class ModerationAction(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'moderation_actions'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    actor_id: uuid.UUID | None
    # Declares this typed field so the surrounding contract is explicit.
    target_user_id: uuid.UUID | None
    # Declares this typed field so the surrounding contract is explicit.
    action: str
    # Declares this typed field so the surrounding contract is explicit.
    reason: str
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AuditEvent`.
class AuditEvent(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'audit_events'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    actor_id: uuid.UUID | None
    # Declares this typed field so the surrounding contract is explicit.
    action: str
    # Declares this typed field so the surrounding contract is explicit.
    target_type: str
    # Declares this typed field so the surrounding contract is explicit.
    target_id: str
    # Stores `reason` because later steps depend on this value.
    reason: str | None = None
    # Stores `event_data` because later steps depend on this value.
    event_data: dict[str, Any] = field(default_factory=dict)
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AdminGrant`.
class AdminGrant(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'admin_grants'
    # Stores `primary_key` because later steps depend on this value.
    primary_key: ClassVar[str] = 'user_id'
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Stores `granted_by` because later steps depend on this value.
    granted_by: uuid.UUID | None = None
    # Stores `granted_at` because later steps depend on this value.
    granted_at: datetime = field(default_factory=utcnow)
    # Stores `revoked_at` because later steps depend on this value.
    revoked_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `SupportRequest`.
class SupportRequest(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'support_requests'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    topic: str
    # Declares this typed field so the surrounding contract is explicit.
    reply_email: str
    # Declares this typed field so the surrounding contract is explicit.
    message: str
    # Stores `status` because later steps depend on this value.
    status: str = 'received'
    # Stores `created_at` because later steps depend on this value.
    created_at: datetime = field(default_factory=utcnow)


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `AccountDeletionRequest`.
class AccountDeletionRequest(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'account_deletion_requests'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID
    # Stores `status` because later steps depend on this value.
    status: str = 'pending'
    # Stores `provider_attempts` because later steps depend on this value.
    provider_attempts: int = 0
    # Stores `last_error_code` because later steps depend on this value.
    last_error_code: str | None = None
    # Stores `requested_at` because later steps depend on this value.
    requested_at: datetime = field(default_factory=utcnow)
    # Stores `last_attempt_at` because later steps depend on this value.
    last_attempt_at: datetime | None = None
    # Stores `completed_at` because later steps depend on this value.
    completed_at: datetime | None = None


# Applies this decorator to configure the declaration immediately below.
@dataclass(kw_only=True, slots=True)
# Groups the state and behavior owned by `ProductEvent`.
class ProductEvent(Document):
    # Stores `collection` because later steps depend on this value.
    collection: ClassVar[str] = 'product_events'
    # Stores `id` because later steps depend on this value.
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Declares this typed field so the surrounding contract is explicit.
    client_event_id: uuid.UUID
    # Declares this typed field so the surrounding contract is explicit.
    event_name: str
    # Declares this typed field so the surrounding contract is explicit.
    anonymous: bool
    # Declares this typed field so the surrounding contract is explicit.
    consent_version: str
    # Declares this typed field so the surrounding contract is explicit.
    release: str
    # Declares this typed field so the surrounding contract is explicit.
    expires_at: datetime
    # Stores `locale` because later steps depend on this value.
    locale: str | None = None
    # Stores `mode` because later steps depend on this value.
    mode: str | None = None
    # Stores `difficulty` because later steps depend on this value.
    difficulty: str | None = None
    # Stores `result` because later steps depend on this value.
    result: str | None = None
    # Stores `attempts_used` because later steps depend on this value.
    attempts_used: int | None = None
    # Stores `ranked` because later steps depend on this value.
    ranked: bool | None = None
    # Stores `score_band` because later steps depend on this value.
    score_band: str | None = None
    # Stores `daily_challenge_id` because later steps depend on this value.
    daily_challenge_id: str | None = None
    # Stores `official` because later steps depend on this value.
    official: bool | None = None
    # Stores `expiry_band` because later steps depend on this value.
    expiry_band: str | None = None
    # Stores `room_state` because later steps depend on this value.
    room_state: str | None = None
    # Stores `reconnect` because later steps depend on this value.
    reconnect: bool | None = None
    # Stores `tie` because later steps depend on this value.
    tie: bool | None = None
    # Stores `validation_category` because later steps depend on this value.
    validation_category: str | None = None
    # Stores `surface` because later steps depend on this value.
    surface: str | None = None
    # Stores `recovered` because later steps depend on this value.
    recovered: bool | None = None
    # Stores `previous_anonymous` because later steps depend on this value.
    previous_anonymous: bool | None = None
    # Stores `occurred_at` because later steps depend on this value.
    occurred_at: datetime = field(default_factory=utcnow)


# Stores `DOCUMENT_TYPES` because later steps depend on this value.
DOCUMENT_TYPES = (
    # Supplies this required nested value.
    Profile,
    # Supplies this required nested value.
    AuthUser,
    # Supplies this required nested value.
    AuthSession,
    # Supplies this required nested value.
    AuthEmailToken,
    # Supplies this required nested value.
    DailyChallenge,
    # Supplies this required nested value.
    FriendChallenge,
    # Supplies this required nested value.
    MultiplayerRoom,
    # Supplies this required nested value.
    GameSession,
    # Supplies this required nested value.
    MultiplayerMember,
    # Supplies this required nested value.
    MultiplayerEvent,
    # Supplies this required nested value.
    LeaderboardEntry,
    # Supplies this required nested value.
    Achievement,
    # Supplies this required nested value.
    UserAchievement,
    # Supplies this required nested value.
    FeatureFlag,
    # Supplies this required nested value.
    ModerationAction,
    # Supplies this required nested value.
    AuditEvent,
    # Supplies this required nested value.
    AdminGrant,
    # Supplies this required nested value.
    SupportRequest,
    # Supplies this required nested value.
    AccountDeletionRequest,
    # Supplies this required nested value.
    ProductEvent,
# Closes the multiline declaration, call, or collection opened above.
)
