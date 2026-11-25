from __future__ import annotations

import uuid
from datetime import UTC, datetime

from mastermind_api.models import LeaderboardEntry, Profile

from .conftest import APIContext


async def test_compound_leaderboard_order_preserves_global_rank_and_private_exclusions(
    api: APIContext,
) -> None:
    current_user = api.current["principal"].user_id
    # Ties must use every documented field, including immutable ID, before pagination.
    cases = [
        (2000, 5, 100, 1),
        (1500, 2, 10, 2),
        (1500, 2, 20, 10),
        (1500, 2, 20, 11),
        (1500, 3, 1, 12),
        (1499, 1, 1, 13),
    ]
    async with api.sessions() as session:
        for index, (score, attempts, elapsed, row_id) in enumerate(cases):
            owner = current_user if index == 3 else uuid.uuid4()
            session.add(Profile(id=owner, display_name=f"Player {index}", public_leaderboards=True))
            session.add(
                LeaderboardEntry(
                    id=uuid.UUID(int=row_id),
                    game_id=uuid.uuid4(),
                    user_id=owner,
                    category="normal",
                    score=score,
                    attempts_used=attempts,
                    elapsed_seconds=elapsed,
                    completed_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            )
        private_user = uuid.uuid4()
        session.add(Profile(id=private_user, public_leaderboards=False))
        session.add(
            LeaderboardEntry(
                game_id=uuid.uuid4(),
                user_id=private_user,
                category="normal",
                score=9999,
                attempts_used=1,
                elapsed_seconds=1,
                completed_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        await session.commit()
    response = await api.client.get("/v1/leaderboards?difficulty=normal&page=2&page_size=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 6
    assert payload["currentUserRank"] == 4
    assert [item["rank"] for item in payload["items"]] == [3, 4]
    assert [item["displayName"] for item in payload["items"]] == ["Player 2", "Player 3"]
    assert payload["items"][1]["isCurrentUser"] is True
