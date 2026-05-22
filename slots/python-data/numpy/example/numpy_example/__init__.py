import numpy as np


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    shifted = x - x.max(axis=axis, keepdims=True)
    e = np.exp(shifted)
    return e / e.sum(axis=axis, keepdims=True)


def cosine(x: np.ndarray, y: np.ndarray) -> float:
    assert x.shape == y.shape, f"shapes differ: {x.shape} vs {y.shape}"
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denom == 0.0:
        return 0.0
    return float(np.dot(x, y) / denom)
