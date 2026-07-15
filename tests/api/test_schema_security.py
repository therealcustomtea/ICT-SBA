from __future__ import annotations

import pytest
from mastermind_api.schemas import CreateChallengeRequest, ProfileUpdateRequest
from pydantic import ValidationError


def test_display_name_normalizes_before_reserved_name_validation() -> None:
    with pytest.raises(ValidationError, match="reserved"):
        ProfileUpdateRequest(display_name="\uff41\uff44\uff4d\uff49\uff4e")


@pytest.mark.parametrize("unsafe", ["Ada\u202e", "Ada\u2066", "Ada\x00"])
def test_user_authored_labels_reject_control_and_bidi_characters(unsafe: str) -> None:
    with pytest.raises(ValidationError, match="control or bidirectional"):
        ProfileUpdateRequest(display_name=unsafe)
    with pytest.raises(ValidationError, match="control or bidirectional"):
        CreateChallengeRequest(difficulty="normal", title=unsafe)


def test_user_authored_labels_are_nfkc_normalized() -> None:
    profile = ProfileUpdateRequest(display_name="  \uff21da   Lovelace  ")
    challenge = CreateChallengeRequest(difficulty="normal", title="  \uff33tudy   room  ")

    assert profile.display_name == "Ada Lovelace"
    assert challenge.title == "Study room"
