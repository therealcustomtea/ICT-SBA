from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(32))
    normalized_display_name: Mapped[str | None] = mapped_column(String(32), unique=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    public_leaderboards: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DailyChallenge(TimestampMixin, Base):
    __tablename__ = "daily_challenges"
    __table_args__ = (UniqueConstraint("challenge_date", "rule_set_version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    challenge_date: Mapped[date] = mapped_column(Date, nullable=False)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    derivation_version: Mapped[str] = mapped_column(String(32), nullable=False)
    derivation_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(32), nullable=False)


class FriendChallenge(TimestampMixin, Base):
    __tablename__ = "friend_challenges"
    __table_args__ = (
        Index("ix_friend_challenges_creator_created", "creator_id", "created_at"),
        Index("ix_friend_challenges_expires", "expires_at"),
        UniqueConstraint(
            "creator_id",
            "creation_idempotency_key",
            name="uq_friend_challenge_creation_idempotency",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    share_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(80))
    show_creator_name: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MultiplayerRoom(TimestampMixin, Base):
    __tablename__ = "multiplayer_rooms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('waiting', 'active', 'completed', 'expired', 'terminated')",
            name="status_allowed",
        ),
        CheckConstraint("event_sequence >= 0", name="event_sequence_nonnegative"),
        Index("ix_multiplayer_rooms_status_expires", "status", "expires_at"),
        Index("ix_multiplayer_rooms_status_updated", "status", "updated_at"),
        UniqueConstraint(
            "owner_id", "creation_idempotency_key", name="uq_room_creation_idempotency"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    room_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="waiting", nullable=False)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL")
    )
    winner_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tie_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_tie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    event_sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GameSession(TimestampMixin, Base):
    __tablename__ = "game_sessions"
    __table_args__ = (
        CheckConstraint("attempts_used >= 0", name="attempts_nonnegative"),
        CheckConstraint("attempts_used <= maximum_attempts", name="attempts_within_limit"),
        CheckConstraint("maximum_attempts >= 1 AND maximum_attempts <= 20", name="attempt_limit"),
        CheckConstraint("invalid_submission_count >= 0", name="invalid_submissions_nonnegative"),
        CheckConstraint(
            "mode IN ('solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel')",
            name="mode_allowed",
        ),
        CheckConstraint(
            "status IN ('created', 'active', 'won', 'lost', 'abandoned', 'expired')",
            name="status_allowed",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert')",
            name="difficulty_allowed",
        ),
        CheckConstraint(
            "ranked_eligibility IN ('eligible', 'unranked', 'invalidated')",
            name="ranked_eligibility_allowed",
        ),
        CheckConstraint(
            "elapsed_seconds IS NULL OR elapsed_seconds >= 0", name="elapsed_nonnegative"
        ),
        CheckConstraint("final_score IS NULL OR final_score >= 0", name="score_nonnegative"),
        CheckConstraint("expires_at > started_at", name="expiry_after_start"),
        Index("ix_game_sessions_owner_created", "owner_id", "created_at"),
        Index("ix_game_sessions_status_mode", "status", "mode"),
        Index("ix_game_sessions_status_expires", "status", "expires_at"),
        Index("ix_game_sessions_completed", "completed_at"),
        Index(
            "ix_game_sessions_friend_completed",
            "friend_challenge_id",
            "completed_at",
        ),
        Index("ix_game_sessions_room", "room_id"),
        UniqueConstraint(
            "owner_id", "creation_idempotency_key", name="uq_game_creation_idempotency"
        ),
        UniqueConstraint("owner_id", "daily_challenge_id", name="uq_daily_official_run"),
        UniqueConstraint("owner_id", "friend_challenge_id", name="uq_friend_official_run"),
        UniqueConstraint("owner_id", "room_id", name="uq_room_member_game"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(80))
    creation_request_fingerprint: Mapped[str | None] = mapped_column(String(64))
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(16))
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_key_version: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maximum_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    final_score: Mapped[int | None] = mapped_column(Integer)
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ranked_eligibility: Mapped[str] = mapped_column(String(24), nullable=False)
    invalidation_reason: Mapped[str | None] = mapped_column(String(200))
    invalid_submission_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("daily_challenges.id", ondelete="RESTRICT")
    )
    friend_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("friend_challenges.id", ondelete="SET NULL")
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("multiplayer_rooms.id", ondelete="SET NULL")
    )
    attempts: Mapped[list[GameAttempt]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="GameAttempt.attempt_number"
    )


class GameAttempt(Base):
    __tablename__ = "game_attempts"
    __table_args__ = (
        UniqueConstraint("game_id", "attempt_number", name="uq_game_attempt_number"),
        UniqueConstraint("game_id", "idempotency_key", name="uq_game_attempt_idempotency"),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        CheckConstraint("black_pegs >= 0 AND white_pegs >= 0", name="feedback_nonnegative"),
        CheckConstraint(
            "black_pegs + white_pegs <= json_array_length(guess)",
            name="feedback_within_code_length",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    guess: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    black_pegs: Mapped[int] = mapped_column(Integer, nullable=False)
    white_pegs: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    game: Mapped[GameSession] = relationship(back_populates="attempts")


class MultiplayerMember(Base):
    __tablename__ = "multiplayer_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MultiplayerEvent(Base):
    __tablename__ = "multiplayer_events"
    __table_args__ = (UniqueConstraint("room_id", "sequence"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LeaderboardEntry(TimestampMixin, Base):
    __tablename__ = "leaderboard_entries"
    __table_args__ = (
        UniqueConstraint("game_id"),
        CheckConstraint("score >= 0", name="score_nonnegative"),
        CheckConstraint("attempts_used >= 1 AND attempts_used <= 20", name="attempts_allowed"),
        CheckConstraint("elapsed_seconds >= 0", name="elapsed_nonnegative"),
        CheckConstraint(
            "review_status IN ('approved', 'pending', 'invalidated', 'deleted_account')",
            name="review_status_allowed",
        ),
        Index("ix_leaderboard_rank", "category", "score", "attempts_used", "elapsed_seconds"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    attempts_used: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), default="approved", nullable=False)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Achievement(Base):
    __tablename__ = "achievements"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        Index("ix_user_achievements_game", "game_id"),
        UniqueConstraint("user_id", "achievement_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    achievement_key: Mapped[str] = mapped_column(
        ForeignKey("achievements.key", ondelete="CASCADE"), nullable=False
    )
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    game_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="SET NULL")
    )


class FeatureFlag(TimestampMixin, Base):
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL")
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(300))
    event_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AdminGrant(Base):
    __tablename__ = "admin_grants"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL")
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportRequest(Base):
    __tablename__ = "support_requests"
    __table_args__ = (Index("ix_support_requests_status_created", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(40), nullable=False)
    reply_email: Mapped[str] = mapped_column(String(254), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="received", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'provider_failed', 'completed')",
            name="status_allowed",
        ),
        CheckConstraint("provider_attempts >= 0", name="provider_attempts_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), server_default="pending", nullable=False)
    provider_attempts: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(40))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProductEvent(Base):
    """Privacy-bounded first-party analytics event with no user identifier or free text."""

    __tablename__ = "product_events"
    __table_args__ = (
        CheckConstraint(
            "event_name IN ('game_started', 'game_completed', 'game_abandoned', "
            "'difficulty_selected', 'daily_completed', 'friend_challenge_created', "
            "'room_joined', 'duel_completed', 'validation_error', 'reconnect', "
            "'account_upgraded')",
            name="event_name_allowed",
        ),
        CheckConstraint("locale IS NULL OR locale IN ('en', 'zh-Hant')", name="locale_allowed"),
        CheckConstraint(
            "mode IS NULL OR mode IN ('solo', 'daily', 'practice', 'pass_and_play', "
            "'friend_challenge', 'duel')",
            name="mode_allowed",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert', 'custom')",
            name="difficulty_allowed",
        ),
        CheckConstraint(
            "result IS NULL OR result IN ('won', 'lost', 'abandoned', 'expired', 'tie')",
            name="result_allowed",
        ),
        CheckConstraint(
            "attempts_used IS NULL OR attempts_used BETWEEN 0 AND 20",
            name="attempts_allowed",
        ),
        CheckConstraint(
            "score_band IS NULL OR score_band IN ('zero', '1-999', '1000-1499', '1500+')",
            name="score_band_allowed",
        ),
        CheckConstraint(
            "expiry_band IS NULL OR expiry_band = '30_days'",
            name="expiry_band_allowed",
        ),
        CheckConstraint(
            "room_state IS NULL OR room_state IN "
            "('waiting', 'active', 'completed', 'expired', 'terminated')",
            name="room_state_allowed",
        ),
        CheckConstraint(
            "validation_category IS NULL OR validation_category IN "
            "('game_config', 'guess', 'challenge', 'room', 'profile', 'auth')",
            name="validation_category_allowed",
        ),
        CheckConstraint(
            "surface IS NULL OR surface IN ('game', 'room', 'daily', 'challenge', 'account')",
            name="surface_allowed",
        ),
        CheckConstraint("expires_at > occurred_at", name="expiry_after_occurrence"),
        Index("ix_product_events_event_occurred", "event_name", "occurred_at"),
        Index("ix_product_events_expires", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_event_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(40), nullable=False)
    anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    release: Mapped[str] = mapped_column(String(64), nullable=False)
    locale: Mapped[str | None] = mapped_column(String(10))
    mode: Mapped[str | None] = mapped_column(String(24))
    difficulty: Mapped[str | None] = mapped_column(String(16))
    result: Mapped[str | None] = mapped_column(String(16))
    attempts_used: Mapped[int | None] = mapped_column(Integer)
    ranked: Mapped[bool | None] = mapped_column(Boolean)
    score_band: Mapped[str | None] = mapped_column(String(16))
    daily_challenge_id: Mapped[str | None] = mapped_column(String(64))
    official: Mapped[bool | None] = mapped_column(Boolean)
    expiry_band: Mapped[str | None] = mapped_column(String(16))
    room_state: Mapped[str | None] = mapped_column(String(16))
    reconnect: Mapped[bool | None] = mapped_column(Boolean)
    tie: Mapped[bool | None] = mapped_column(Boolean)
    validation_category: Mapped[str | None] = mapped_column(String(24))
    surface: Mapped[str | None] = mapped_column(String(16))
    recovered: Mapped[bool | None] = mapped_column(Boolean)
    previous_anonymous: Mapped[bool | None] = mapped_column(Boolean)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
