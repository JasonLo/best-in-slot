import torch
from torch import nn


def make_model(in_dim: int = 8, out_dim: int = 2) -> nn.Module:
    return nn.Sequential(nn.Linear(in_dim, 16), nn.ReLU(), nn.Linear(16, out_dim))


def _learnable_batch(batch: int = 64, in_dim: int = 8) -> tuple[torch.Tensor, torch.Tensor]:
    """Deterministic toy dataset: label = 1 iff the first feature is positive."""
    x = torch.randn(batch, in_dim)
    y = (x[:, 0] > 0).long()
    return x, y


def train_one_step(model: nn.Module, opt: torch.optim.Optimizer) -> float:
    x, y = _learnable_batch()
    logits = model(x)
    loss = nn.functional.cross_entropy(logits, y)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    opt.step()
    return float(loss.item())
