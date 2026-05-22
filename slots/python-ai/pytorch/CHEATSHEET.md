# pytorch cheatsheet

## Install via uv (CPU)

```toml
[project]
dependencies = ["torch>=2.5", "torchvision>=0.20"]
```

## Install via uv (CUDA 12.8 — matches matryoshka-weights)

```toml
[project]
dependencies = ["torch>=2.10", "torchvision>=0.25"]

[tool.uv.sources]
torch = [{ index = "pytorch-cu128", marker = "sys_platform == 'linux'" }]
torchvision = [{ index = "pytorch-cu128", marker = "sys_platform == 'linux'" }]

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```

## Device selection

```python
import torch
device = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
```

## Tiny training loop

```python
import torch
from torch import nn

torch.manual_seed(0)
model = nn.Linear(8, 2).to(device)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

for step in range(100):
    x = torch.randn(32, 8, device=device)
    y = torch.randint(0, 2, (32,), device=device)
    logits = model(x)
    loss = loss_fn(logits, y)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    opt.step()
```

## Mixed precision + compile

```python
model = torch.compile(model)
with torch.autocast("cuda", dtype=torch.bfloat16):
    out = model(x)
```

## Save / load

```python
torch.save({"model": model.state_dict(), "step": step}, "ckpt.pt")

ck = torch.load("ckpt.pt", map_location="cpu", weights_only=True)
model.load_state_dict(ck["model"])
```

## Reproducibility

```python
import numpy as np, random, torch
SEED = 0
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
```
