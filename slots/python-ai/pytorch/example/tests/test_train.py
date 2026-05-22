import torch

from pytorch_example import make_model, train_one_step


def test_loss_decreases_over_steps() -> None:
    torch.manual_seed(0)
    model = make_model()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-2)
    first = train_one_step(model, opt)
    for _ in range(50):
        last = train_one_step(model, opt)
    assert last < first
