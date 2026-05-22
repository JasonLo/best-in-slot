import pytest
from pydantic import ValidationError

from pydantic_example import User


def test_lowercases_email() -> None:
    u = User.model_validate({"id": 1, "name": "Jason", "email": "J@WISC.EDU"})
    assert u.email == "j@wisc.edu"


def test_strict_rejects_string_id() -> None:
    with pytest.raises(ValidationError):
        User.model_validate({"id": "1", "name": "Jason"})


def test_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        User.model_validate({"id": 1, "name": "Jason", "rogue": True})
