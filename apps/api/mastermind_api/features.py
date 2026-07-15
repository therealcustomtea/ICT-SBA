from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .models import FeatureFlag

ENVIRONMENT_FLAGS = {
    "daily": "feature_daily",
    "leaderboards": "feature_leaderboards",
    "friend_challenges": "feature_friend_challenges",
    "multiplayer": "feature_multiplayer",
    "achievements": "feature_achievements",
    "account_registration": "feature_account_registration",
    "analytics": "feature_analytics",
}


async def feature_enabled(session: AsyncSession, settings: Settings, key: str) -> bool:
    setting_name = ENVIRONMENT_FLAGS.get(key)
    if setting_name is not None and not bool(getattr(settings, setting_name)):
        return False
    database_flag = await session.get(FeatureFlag, key)
    return database_flag.enabled if database_flag is not None else True
