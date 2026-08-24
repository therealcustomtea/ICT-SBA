# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import date, datetime

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import (
    # Supplies this item to the surrounding call or collection.
    JSON,
    # Supplies this item to the surrounding call or collection.
    Boolean,
    # Supplies this item to the surrounding call or collection.
    CheckConstraint,
    # Supplies this item to the surrounding call or collection.
    Date,
    # Supplies this item to the surrounding call or collection.
    DateTime,
    # Supplies this item to the surrounding call or collection.
    ForeignKey,
    # Supplies this item to the surrounding call or collection.
    Index,
    # Supplies this item to the surrounding call or collection.
    Integer,
    # Supplies this item to the surrounding call or collection.
    LargeBinary,
    # Supplies this item to the surrounding call or collection.
    String,
    # Supplies this item to the surrounding call or collection.
    Text,
    # Supplies this item to the surrounding call or collection.
    UniqueConstraint,
    # Supplies this item to the surrounding call or collection.
    Uuid,
    # Supplies this item to the surrounding call or collection.
    func,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `sqlalchemy.orm` for use in this module.
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Imports selected names from `.database` for use in this module.
from .database import Base


# Defines the `TimestampMixin` class and its related behavior.
class TimestampMixin:
    # Computes and stores `created_at` for subsequent operations.
    created_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `updated_at` for subsequent operations.
    updated_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `onupdate` value to the surrounding call.
        onupdate=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `Profile` class and its related behavior.
class Profile(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "profiles"

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # Computes and stores `display_name` for subsequent operations.
    display_name: Mapped[str | None] = mapped_column(String(32))
    # Computes and stores `normalized_display_name` for subsequent operations.
    normalized_display_name: Mapped[str | None] = mapped_column(String(32), unique=True)
    # Computes and stores `is_anonymous` for subsequent operations.
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Computes and stores `public_leaderboards` for subsequent operations.
    public_leaderboards: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Computes and stores `is_banned` for subsequent operations.
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Computes and stores `deleted_at` for subsequent operations.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Defines the `DailyChallenge` class and its related behavior.
class DailyChallenge(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "daily_challenges"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (UniqueConstraint("challenge_date", "rule_set_version"),)

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `challenge_date` for subsequent operations.
    challenge_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Computes and stores `public_id` for subsequent operations.
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # Computes and stores `config` for subsequent operations.
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Computes and stores `derivation_version` for subsequent operations.
    derivation_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `derivation_key_version` for subsequent operations.
    derivation_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `rule_set_version` for subsequent operations.
    rule_set_version: Mapped[str] = mapped_column(String(32), nullable=False)


# Defines the `FriendChallenge` class and its related behavior.
class FriendChallenge(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "friend_challenges"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `Index` with the supplied values.
        Index("ix_friend_challenges_creator_created", "creator_id", "created_at"),
        # Calls `Index` with the supplied values.
        Index("ix_friend_challenges_expires", "expires_at"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint(
            # Supplies this item to the surrounding call or collection.
            "creator_id",
            # Supplies this item to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` parameter or keyword argument.
            name="uq_friend_challenge_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `share_code_hash` for subsequent operations.
    share_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Computes and stores `creation_idempotency_key` for subsequent operations.
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    # Computes and stores `creation_request_fingerprint` for subsequent operations.
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    # Computes and stores `creator_id` for subsequent operations.
    creator_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `title` for subsequent operations.
    title: Mapped[str | None] = mapped_column(String(80))
    # Computes and stores `show_creator_name` for subsequent operations.
    show_creator_name: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Computes and stores `config` for subsequent operations.
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Computes and stores `encrypted_secret` for subsequent operations.
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_nonce` for subsequent operations.
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_key_version` for subsequent operations.
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `revoked_at` for subsequent operations.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Computes and stores `expires_at` for subsequent operations.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# Defines the `MultiplayerRoom` class and its related behavior.
class MultiplayerRoom(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "multiplayer_rooms"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('waiting', 'active', 'completed', 'expired', 'terminated')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("event_sequence >= 0", name="event_sequence_nonnegative"),
        # Calls `Index` with the supplied values.
        Index("ix_multiplayer_rooms_status_expires", "status", "expires_at"),
        # Calls `Index` with the supplied values.
        Index("ix_multiplayer_rooms_status_updated", "status", "updated_at"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Supplies this string to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` value to the surrounding call.
            name="uq_room_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `room_code_hash` for subsequent operations.
    room_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Computes and stores `creation_idempotency_key` for subsequent operations.
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    # Computes and stores `creation_request_fingerprint` for subsequent operations.
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    # Computes and stores `owner_id` for subsequent operations.
    owner_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `config` for subsequent operations.
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Computes and stores `encrypted_secret` for subsequent operations.
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_nonce` for subsequent operations.
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_key_version` for subsequent operations.
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `status` for subsequent operations.
    status: Mapped[str] = mapped_column(String(24), default="waiting", nullable=False)
    # Computes and stores `winner_id` for subsequent operations.
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `winner_at` for subsequent operations.
    winner_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Computes and stores `tie_deadline` for subsequent operations.
    tie_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Computes and stores `is_tie` for subsequent operations.
    is_tie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Computes and stores `event_sequence` for subsequent operations.
    event_sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Computes and stores `expires_at` for subsequent operations.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# Defines the `GameSession` class and its related behavior.
class GameSession(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "game_sessions"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("attempts_used >= 0", name="attempts_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("attempts_used <= maximum_attempts", name="attempts_within_limit"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("maximum_attempts >= 1 AND maximum_attempts <= 20", name="attempt_limit"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("invalid_submission_count >= 0", name="invalid_submissions_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "mode IN ('solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel')",
            # Provides the `name` parameter or keyword argument.
            name="mode_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('created', 'active', 'won', 'lost', 'abandoned', 'expired')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert')",
            # Provides the `name` parameter or keyword argument.
            name="difficulty_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "ranked_eligibility IN ('eligible', 'unranked', 'invalidated')",
            # Provides the `name` parameter or keyword argument.
            name="ranked_eligibility_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "elapsed_seconds IS NULL OR elapsed_seconds >= 0",
            # Provides the `name` value to the surrounding call.
            name="elapsed_nonnegative",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("final_score IS NULL OR final_score >= 0", name="score_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("expires_at > started_at", name="expiry_after_start"),
        # Calls `Index` with the supplied values.
        Index("ix_game_sessions_owner_created", "owner_id", "created_at"),
        # Calls `Index` with the supplied values.
        Index("ix_game_sessions_status_mode", "status", "mode"),
        # Calls `Index` with the supplied values.
        Index("ix_game_sessions_status_expires", "status", "expires_at"),
        # Calls `Index` with the supplied values.
        Index("ix_game_sessions_completed", "completed_at"),
        # Calls `Index` with the supplied values.
        Index(
            # Supplies this item to the surrounding call or collection.
            "ix_game_sessions_friend_completed",
            # Supplies this item to the surrounding call or collection.
            "friend_challenge_id",
            # Supplies this item to the surrounding call or collection.
            "completed_at",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `Index` with the supplied values.
        Index("ix_game_sessions_room", "room_id"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Supplies this string to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` value to the surrounding call.
            name="uq_game_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("owner_id", "daily_challenge_id", name="uq_daily_official_run"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("owner_id", "friend_challenge_id", name="uq_friend_official_run"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("owner_id", "room_id", name="uq_room_member_game"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `public_id` for subsequent operations.
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # Computes and stores `creation_idempotency_key` for subsequent operations.
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    # Computes and stores `creation_request_fingerprint` for subsequent operations.
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    # Computes and stores `owner_id` for subsequent operations.
    owner_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `mode` for subsequent operations.
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `config` for subsequent operations.
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Computes and stores `status` for subsequent operations.
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    # Computes and stores `rule_set_version` for subsequent operations.
    rule_set_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `scoring_version` for subsequent operations.
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `encrypted_secret` for subsequent operations.
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_nonce` for subsequent operations.
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Computes and stores `secret_key_version` for subsequent operations.
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `attempts_used` for subsequent operations.
    attempts_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Computes and stores `maximum_attempts` for subsequent operations.
    maximum_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `started_at` for subsequent operations.
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Computes and stores `expires_at` for subsequent operations.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Computes and stores `completed_at` for subsequent operations.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Computes and stores `elapsed_seconds` for subsequent operations.
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    # Computes and stores `final_score` for subsequent operations.
    final_score: Mapped[int | None] = mapped_column(Integer)
    # Computes and stores `score_breakdown` for subsequent operations.
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    # Computes and stores `ranked_eligibility` for subsequent operations.
    ranked_eligibility: Mapped[str] = mapped_column(String(24), nullable=False)
    # Computes and stores `invalidation_reason` for subsequent operations.
    invalidation_reason: Mapped[str | None] = mapped_column(String(200))
    # Computes and stores `invalid_submission_count` for subsequent operations.
    invalid_submission_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Computes and stores `daily_challenge_id` for subsequent operations.
    daily_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("daily_challenges.id", ondelete="RESTRICT")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `friend_challenge_id` for subsequent operations.
    friend_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("friend_challenges.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `room_id` for subsequent operations.
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("multiplayer_rooms.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `attempts` for subsequent operations.
    attempts: Mapped[list[GameAttempt]] = relationship(
        # Computes and stores `back_populates` for subsequent operations.
        back_populates="game",
        # Provides the `cascade` value to the surrounding call.
        cascade="all, delete-orphan",
        # Provides the `order_by` value to the surrounding call.
        order_by="GameAttempt.attempt_number",
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `GameAttempt` class and its related behavior.
class GameAttempt(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "game_attempts"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("game_id", "attempt_number", name="uq_game_attempt_number"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("game_id", "idempotency_key", name="uq_game_attempt_idempotency"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("black_pegs >= 0 AND white_pegs >= 0", name="feedback_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "black_pegs + white_pegs <= json_array_length(guess)",
            # Provides the `name` parameter or keyword argument.
            name="feedback_within_code_length",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `game_id` for subsequent operations.
    game_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `attempt_number` for subsequent operations.
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `guess` for subsequent operations.
    guess: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    # Computes and stores `black_pegs` for subsequent operations.
    black_pegs: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `white_pegs` for subsequent operations.
    white_pegs: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `submitted_at` for subsequent operations.
    submitted_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    # Computes and stores `request_id` for subsequent operations.
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # Computes and stores `game` for subsequent operations.
    game: Mapped[GameSession] = relationship(back_populates="attempts")


# Defines the `MultiplayerMember` class and its related behavior.
class MultiplayerMember(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "multiplayer_members"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (UniqueConstraint("room_id", "user_id"),)

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `room_id` for subsequent operations.
    room_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `joined_at` for subsequent operations.
    joined_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `last_seen_at` for subsequent operations.
    last_seen_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `connected` for subsequent operations.
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Computes and stores `ready` for subsequent operations.
    ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Computes and stores `ready_at` for subsequent operations.
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Defines the `MultiplayerEvent` class and its related behavior.
class MultiplayerEvent(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "multiplayer_events"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (UniqueConstraint("room_id", "sequence"),)

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `room_id` for subsequent operations.
    room_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `sequence` for subsequent operations.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `event_type` for subsequent operations.
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # Computes and stores `payload` for subsequent operations.
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Computes and stores `created_at` for subsequent operations.
    created_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `LeaderboardEntry` class and its related behavior.
class LeaderboardEntry(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "leaderboard_entries"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("game_id"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("score >= 0", name="score_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("attempts_used >= 1 AND attempts_used <= 20", name="attempts_allowed"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("elapsed_seconds >= 0", name="elapsed_nonnegative"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "review_status IN ('approved', 'pending', 'invalidated', 'deleted_account')",
            # Provides the `name` parameter or keyword argument.
            name="review_status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `Index` with the supplied values.
        Index("ix_leaderboard_rank", "category", "score", "attempts_used", "elapsed_seconds"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `game_id` for subsequent operations.
    game_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `category` for subsequent operations.
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    # Computes and stores `score` for subsequent operations.
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `attempts_used` for subsequent operations.
    attempts_used: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `elapsed_seconds` for subsequent operations.
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computes and stores `completed_at` for subsequent operations.
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Computes and stores `review_status` for subsequent operations.
    review_status: Mapped[str] = mapped_column(String(24), default="approved", nullable=False)
    # Computes and stores `invalidated_at` for subsequent operations.
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Defines the `Achievement` class and its related behavior.
class Achievement(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "achievements"

    # Computes and stores `key` for subsequent operations.
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    # Computes and stores `version` for subsequent operations.
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Computes and stores `name` for subsequent operations.
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # Computes and stores `description` for subsequent operations.
    description: Mapped[str] = mapped_column(String(200), nullable=False)


# Defines the `UserAchievement` class and its related behavior.
class UserAchievement(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "user_achievements"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `Index` with the supplied values.
        Index("ix_user_achievements_game", "game_id"),
        # Calls `UniqueConstraint` with the supplied values.
        UniqueConstraint("user_id", "achievement_key"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `achievement_key` for subsequent operations.
    achievement_key: Mapped[str] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("achievements.key", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `awarded_at` for subsequent operations.
    awarded_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game_id` for subsequent operations.
    game_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("game_sessions.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `FeatureFlag` class and its related behavior.
class FeatureFlag(TimestampMixin, Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "feature_flags"

    # Computes and stores `key` for subsequent operations.
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Computes and stores `enabled` for subsequent operations.
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Computes and stores `description` for subsequent operations.
    description: Mapped[str | None] = mapped_column(String(200))


# Defines the `ModerationAction` class and its related behavior.
class ModerationAction(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "moderation_actions"

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `actor_id` for subsequent operations.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `target_user_id` for subsequent operations.
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `action` for subsequent operations.
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `reason` for subsequent operations.
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    # Computes and stores `created_at` for subsequent operations.
    created_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `AuditEvent` class and its related behavior.
class AuditEvent(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "audit_events"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (Index("ix_audit_events_created", "created_at"),)

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `actor_id` for subsequent operations.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `action` for subsequent operations.
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    # Computes and stores `target_type` for subsequent operations.
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # Computes and stores `target_id` for subsequent operations.
    target_id: Mapped[str] = mapped_column(String(80), nullable=False)
    # Computes and stores `reason` for subsequent operations.
    reason: Mapped[str | None] = mapped_column(String(300))
    # Computes and stores `event_data` for subsequent operations.
    event_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    # Computes and stores `created_at` for subsequent operations.
    created_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `AdminGrant` class and its related behavior.
class AdminGrant(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "admin_grants"

    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `primary_key` value to the surrounding call.
        primary_key=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `granted_by` for subsequent operations.
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="SET NULL")
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `granted_at` for subsequent operations.
    granted_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `revoked_at` for subsequent operations.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Defines the `SupportRequest` class and its related behavior.
class SupportRequest(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "support_requests"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (Index("ix_support_requests_status_created", "status", "created_at"),)

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(
        # Calls `ForeignKey` with the supplied values.
        ForeignKey("profiles.id", ondelete="CASCADE"),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `topic` for subsequent operations.
    topic: Mapped[str] = mapped_column(String(40), nullable=False)
    # Computes and stores `reply_email` for subsequent operations.
    reply_email: Mapped[str] = mapped_column(String(254), nullable=False)
    # Computes and stores `message` for subsequent operations.
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Computes and stores `status` for subsequent operations.
    status: Mapped[str] = mapped_column(String(20), default="received", nullable=False)
    # Computes and stores `created_at` for subsequent operations.
    created_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `AccountDeletionRequest` class and its related behavior.
class AccountDeletionRequest(Base):
    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "account_deletion_requests"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('pending', 'provider_failed', 'completed')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("provider_attempts >= 0", name="provider_attempts_nonnegative"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `user_id` for subsequent operations.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    # Computes and stores `status` for subsequent operations.
    status: Mapped[str] = mapped_column(String(24), server_default="pending", nullable=False)
    # Computes and stores `provider_attempts` for subsequent operations.
    provider_attempts: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    # Computes and stores `last_error_code` for subsequent operations.
    last_error_code: Mapped[str | None] = mapped_column(String(40))
    # Computes and stores `requested_at` for subsequent operations.
    requested_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `last_attempt_at` for subsequent operations.
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Computes and stores `completed_at` for subsequent operations.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Defines the `ProductEvent` class and its related behavior.
class ProductEvent(Base):
    # Documents the purpose or contract of this module, class, or function.
    """Privacy-bounded first-party analytics event with no user identifier or free text."""

    # Computes and stores `__tablename__` for subsequent operations.
    __tablename__ = "product_events"
    # Computes and stores `__table_args__` for subsequent operations.
    __table_args__ = (
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "event_name IN ('game_started', 'game_completed', 'game_abandoned', "
            # Executes this statement as the next step in the surrounding logic.
            "'difficulty_selected', 'daily_completed', 'friend_challenge_created', "
            # Executes this statement as the next step in the surrounding logic.
            "'room_joined', 'duel_completed', 'validation_error', 'reconnect', "
            # Supplies this item to the surrounding call or collection.
            "'account_upgraded')",
            # Provides the `name` parameter or keyword argument.
            name="event_name_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("locale IS NULL OR locale IN ('en', 'zh-Hant')", name="locale_allowed"),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "mode IS NULL OR mode IN ('solo', 'daily', 'practice', 'pass_and_play', "
            # Supplies this item to the surrounding call or collection.
            "'friend_challenge', 'duel')",
            # Provides the `name` parameter or keyword argument.
            name="mode_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert', 'custom')",
            # Provides the `name` parameter or keyword argument.
            name="difficulty_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "result IS NULL OR result IN ('won', 'lost', 'abandoned', 'expired', 'tie')",
            # Provides the `name` parameter or keyword argument.
            name="result_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "attempts_used IS NULL OR attempts_used BETWEEN 0 AND 20",
            # Provides the `name` parameter or keyword argument.
            name="attempts_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "score_band IS NULL OR score_band IN ('zero', '1-999', '1000-1499', '1500+')",
            # Provides the `name` parameter or keyword argument.
            name="score_band_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "expiry_band IS NULL OR expiry_band = '30_days'",
            # Provides the `name` parameter or keyword argument.
            name="expiry_band_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "room_state IS NULL OR room_state IN "
            # Supplies this item to the surrounding call or collection.
            "('waiting', 'active', 'completed', 'expired', 'terminated')",
            # Provides the `name` parameter or keyword argument.
            name="room_state_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "validation_category IS NULL OR validation_category IN "
            # Supplies this item to the surrounding call or collection.
            "('game_config', 'guess', 'challenge', 'room', 'profile', 'auth')",
            # Provides the `name` parameter or keyword argument.
            name="validation_category_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "surface IS NULL OR surface IN ('game', 'room', 'daily', 'challenge', 'account')",
            # Provides the `name` parameter or keyword argument.
            name="surface_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `CheckConstraint` with the supplied values.
        CheckConstraint("expires_at > occurred_at", name="expiry_after_occurrence"),
        # Calls `Index` with the supplied values.
        Index("ix_product_events_event_occurred", "event_name", "occurred_at"),
        # Calls `Index` with the supplied values.
        Index("ix_product_events_expires", "expires_at"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Computes and stores `id` for subsequent operations.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Computes and stores `client_event_id` for subsequent operations.
    client_event_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    # Computes and stores `event_name` for subsequent operations.
    event_name: Mapped[str] = mapped_column(String(40), nullable=False)
    # Computes and stores `anonymous` for subsequent operations.
    anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Computes and stores `consent_version` for subsequent operations.
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Computes and stores `release` for subsequent operations.
    release: Mapped[str] = mapped_column(String(64), nullable=False)
    # Computes and stores `locale` for subsequent operations.
    locale: Mapped[str | None] = mapped_column(String(10))
    # Computes and stores `mode` for subsequent operations.
    mode: Mapped[str | None] = mapped_column(String(24))
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `result` for subsequent operations.
    result: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `attempts_used` for subsequent operations.
    attempts_used: Mapped[int | None] = mapped_column(Integer)
    # Computes and stores `ranked` for subsequent operations.
    ranked: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `score_band` for subsequent operations.
    score_band: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `daily_challenge_id` for subsequent operations.
    daily_challenge_id: Mapped[str | None] = mapped_column(String(64))
    # Computes and stores `official` for subsequent operations.
    official: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `expiry_band` for subsequent operations.
    expiry_band: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `room_state` for subsequent operations.
    room_state: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `reconnect` for subsequent operations.
    reconnect: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `tie` for subsequent operations.
    tie: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `validation_category` for subsequent operations.
    validation_category: Mapped[str | None] = mapped_column(String(24))
    # Computes and stores `surface` for subsequent operations.
    surface: Mapped[str | None] = mapped_column(String(16))
    # Computes and stores `recovered` for subsequent operations.
    recovered: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `previous_anonymous` for subsequent operations.
    previous_anonymous: Mapped[bool | None] = mapped_column(Boolean)
    # Computes and stores `occurred_at` for subsequent operations.
    occurred_at: Mapped[datetime] = mapped_column(
        # Calls `DateTime` with the supplied values.
        DateTime(timezone=True),
        # Provides the `server_default` value to the surrounding call.
        server_default=func.now(),
        # Provides the `nullable` value to the surrounding call.
        nullable=False,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `expires_at` for subsequent operations.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
