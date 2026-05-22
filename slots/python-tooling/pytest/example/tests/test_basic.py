import pytest

from pytest_example import add


def test_add() -> None:
    assert add(1, 2) == 3


@pytest.mark.parametrize("a,b,expected", [(0, 0, 0), (-1, 1, 0), (10, 20, 30)])
def test_add_params(a: int, b: int, expected: int) -> None:
    assert add(a, b) == expected
