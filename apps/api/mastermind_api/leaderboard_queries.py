# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `typing` for this module.
from typing import Any

# Imports the required names from `.database` for this module.
from .database import MongoSession

# Imports the required names from `.models` for this module.
from .models import LeaderboardEntry


# Defines this callable to implement the operation described by its name.
async def ranked_leaderboard_page(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Supplies this required nested value.
    *,
    # Declares this typed field so the surrounding contract is explicit.
    match: dict[str, Any],
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    page: int,
    # Declares this typed field so the surrounding contract is explicit.
    page_size: int,
# Closes the multiline declaration, call, or collection opened above.
) -> tuple[list[dict[str, Any]], int, int | None]:
    # Stores `pipeline` because later steps depend on this value.
    pipeline: list[dict[str, Any]] = [
        # Supplies this required nested value.
        {'$match': match},
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            '$lookup': {
                # Supplies this literal value to the surrounding declaration or call.
                'from': 'profiles',
                # Supplies this literal value to the surrounding declaration or call.
                'localField': 'user_id',
                # Supplies this literal value to the surrounding declaration or call.
                'foreignField': '_id',
                # Supplies this literal value to the surrounding declaration or call.
                'as': 'profile',
            # Closes the multiline declaration, call, or collection opened above.
            }
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Supplies this required nested value.
        {'$unwind': '$profile'},
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            '$match': {
                # Supplies this literal value to the surrounding declaration or call.
                'profile.deleted_at': None,
                # Supplies this literal value to the surrounding declaration or call.
                'profile.is_banned': False,
                # Supplies this literal value to the surrounding declaration or call.
                'profile.public_leaderboards': True,
            # Closes the multiline declaration, call, or collection opened above.
            }
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            '$setWindowFields': {
                # Supplies this literal value to the surrounding declaration or call.
                'sortBy': {
                    # Supplies this literal value to the surrounding declaration or call.
                    'score': -1,
                    # Supplies this literal value to the surrounding declaration or call.
                    'attempts_used': 1,
                    # Supplies this literal value to the surrounding declaration or call.
                    'elapsed_seconds': 1,
                    # Supplies this literal value to the surrounding declaration or call.
                    'completed_at': 1,
                    # Supplies this literal value to the surrounding declaration or call.
                    '_id': 1,
                # Closes the multiline declaration, call, or collection opened above.
                },
                # Supplies this literal value to the surrounding declaration or call.
                'output': {'rank': {'$documentNumber': {}}},
            # Closes the multiline declaration, call, or collection opened above.
            }
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            '$facet': {
                # Supplies this literal value to the surrounding declaration or call.
                'items': [
                    # Supplies this required nested value.
                    {'$skip': (page - 1) * page_size},
                    # Supplies this required nested value.
                    {'$limit': page_size},
                    # Supplies this required nested value.
                    {
                        # Supplies this literal value to the surrounding declaration or call.
                        '$project': {
                            # Supplies this literal value to the surrounding declaration or call.
                            'user_id': 1,
                            # Supplies this literal value to the surrounding declaration or call.
                            'score': 1,
                            # Supplies this literal value to the surrounding declaration or call.
                            'attempts_used': 1,
                            # Supplies this literal value to the surrounding declaration or call.
                            'elapsed_seconds': 1,
                            # Supplies this literal value to the surrounding declaration or call.
                            'completed_at': 1,
                            # Supplies this literal value to the surrounding declaration or call.
                            'display_name': '$profile.display_name',
                            # Supplies this literal value to the surrounding declaration or call.
                            'rank': 1,
                        # Closes the multiline declaration, call, or collection opened above.
                        }
                    # Closes the multiline declaration, call, or collection opened above.
                    },
                # Closes the multiline declaration, call, or collection opened above.
                ],
                # Supplies this literal value to the surrounding declaration or call.
                'metadata': [{'$count': 'total'}],
                # Supplies this literal value to the surrounding declaration or call.
                'current_user': [
                    # Supplies this required nested value.
                    {'$match': {'user_id': user_id}},
                    # Supplies this required nested value.
                    {'$limit': 1},
                    # Supplies this required nested value.
                    {'$project': {'rank': 1}},
                # Closes the multiline declaration, call, or collection opened above.
                ],
            # Closes the multiline declaration, call, or collection opened above.
            }
        # Closes the multiline declaration, call, or collection opened above.
        },
    # Closes the multiline declaration, call, or collection opened above.
    ]
    # Stores `result` because later steps depend on this value.
    result = await session.aggregate(LeaderboardEntry, pipeline)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if not result:
        # Returns the computed result and ends the current callable.
        return [], 0, None
    # Stores `page_result` because later steps depend on this value.
    page_result = result[0]
    # Stores `metadata` because later steps depend on this value.
    metadata = page_result.get('metadata', [])
    # Stores `current_user` because later steps depend on this value.
    current_user = page_result.get('current_user', [])
    # Returns the computed result and ends the current callable.
    return (
        # Supplies this required nested value.
        page_result.get('items', []),
        # Supplies this required nested value.
        metadata[0]['total'] if metadata else 0,
        # Supplies this required nested value.
        current_user[0]['rank'] if current_user else None,
    # Closes the multiline declaration, call, or collection opened above.
    )
