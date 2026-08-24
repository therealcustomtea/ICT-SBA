# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `.config` for use in this module.
from .config import Settings

# Imports selected names from `.models` for use in this module.
from .models import FeatureFlag

# Computes and stores `ENVIRONMENT_FLAGS` for subsequent operations.
ENVIRONMENT_FLAGS = {
    # Associates the `daily` key with its value.
    "daily": "feature_daily",
    # Associates the `leaderboards` key with its value.
    "leaderboards": "feature_leaderboards",
    # Associates the `friend_challenges` key with its value.
    "friend_challenges": "feature_friend_challenges",
    # Associates the `multiplayer` key with its value.
    "multiplayer": "feature_multiplayer",
    # Associates the `achievements` key with its value.
    "achievements": "feature_achievements",
    # Associates the `account_registration` key with its value.
    "account_registration": "feature_account_registration",
    # Associates the `analytics` key with its value.
    "analytics": "feature_analytics",
    # Closes the multiline call, declaration, or collection started above.
}


# Defines the `feature_enabled` callable and its typed interface.
async def feature_enabled(session: AsyncSession, settings: Settings, key: str) -> bool:
    # Computes and stores `setting_name` for subsequent operations.
    setting_name = ENVIRONMENT_FLAGS.get(key)
    # Checks this condition before executing the nested branch.
    if setting_name is not None and not bool(getattr(settings, setting_name)):
        # Returns this result to the caller and ends the current function.
        return False
    # Computes and stores `database_flag` for subsequent operations.
    database_flag = await session.get(FeatureFlag, key)
    # Returns this result to the caller and ends the current function.
    return database_flag.enabled if database_flag is not None else True
