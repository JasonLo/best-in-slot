import numpy as np

from numpy_example import cosine, softmax


def test_softmax_sums_to_one() -> None:
    x = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
    out = softmax(x, axis=-1)
    assert np.allclose(out.sum(axis=-1), 1.0)


def test_cosine_identity() -> None:
    v = np.array([1.0, 2.0, 3.0])
    assert cosine(v, v) == 1.0


def test_cosine_orthogonal() -> None:
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert cosine(a, b) == 0.0
