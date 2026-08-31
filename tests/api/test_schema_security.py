# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.schemas` for use in this module.
from mastermind_api.schemas import CreateChallengeRequest, ProfileUpdateRequest

# Imports selected names from `pydantic` for use in this module.
from pydantic import ValidationError


# Defines the `test_display_name_normalizes_before_reserved_name_validation` callable and its typed
# interface.
def test_display_name_normalizes_before_reserved_name_validation() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValidationError, match="reserved"):
        # Calls `ProfileUpdateRequest` with the supplied values.
        ProfileUpdateRequest(display_name="\uff41\uff44\uff4d\uff49\uff4e")


# Applies `@pytest.mark.parametrize("unsafe", ["Ada\u202e", "Ada\u2066", "Ada\x00"])` to configure
# the declaration immediately below.
@pytest.mark.parametrize("unsafe", ["Ada\u202e", "Ada\u2066", "Ada\x00"])
# Defines the `test_user_authored_labels_reject_control_and_bidi_characters` callable and its typed
# interface.
def test_user_authored_labels_reject_control_and_bidi_characters(unsafe: str) -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValidationError, match="control or bidirectional"):
        # Calls `ProfileUpdateRequest` with the supplied values.
        ProfileUpdateRequest(display_name=unsafe)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValidationError, match="control or bidirectional"):
        # Calls `CreateChallengeRequest` with the supplied values.
        CreateChallengeRequest(difficulty="normal", title=unsafe)


# Defines the `test_user_authored_labels_are_nfkc_normalized` callable and its typed interface.
def test_user_authored_labels_are_nfkc_normalized() -> None:
    # Computes and stores `profile` for subsequent operations.
    profile = ProfileUpdateRequest(display_name="  \uff21da   Lovelace  ")
    # Computes and stores `challenge` for subsequent operations.
    challenge = CreateChallengeRequest(difficulty="normal", title="  \uff33tudy   room  ")

    # Asserts this invariant so an unexpected test state fails immediately.
    assert profile.display_name == "Ada Lovelace"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert challenge.title == "Study room"
