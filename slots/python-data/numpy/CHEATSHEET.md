# numpy cheatsheet

## Create

```python
import numpy as np

a = np.zeros((3, 4), dtype=np.float32)
b = np.arange(10)
c = np.linspace(0, 1, 100)
rng = np.random.default_rng(seed=0)
d = rng.standard_normal((1000,))
```

## Index / slice

```python
a[0, :]            # first row
a[:, 1]            # second column
a[a > 0]           # boolean mask (returns 1-D)
a[[0, 2], :]       # fancy index
```

## Math

```python
(a + 1).clip(0, None)
np.where(a > 0, a, 0)         # ReLU
np.linalg.norm(a, axis=1)
softmax = np.exp(a) / np.exp(a).sum(axis=-1, keepdims=True)
```

## Shapes (assert at boundaries)

```python
def cosine(x: np.ndarray, y: np.ndarray) -> float:
    assert x.shape == y.shape == (D,)
    return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y)))
```

## Save / load

```python
np.save("data.npy", a)
np.savez_compressed("bundle.npz", a=a, b=b)
loaded = np.load("data.npy")
```

## Interop

```python
import torch
t = torch.from_numpy(a)            # no copy when possible
back = t.numpy()
```
