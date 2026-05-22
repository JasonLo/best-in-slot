import pytest


def test_generate_or_skip_offline() -> None:
    """Verify generation runs. Skip cleanly when this host can't reach huggingface.co."""
    try:
        from transformers_example import generate

        out = generate("Once upon a time", max_new_tokens=4)
    except OSError as e:
        msg = str(e).lower()
        if "couldn't connect" in msg or "could not connect" in msg or "connection" in msg:
            pytest.skip(f"offline / HF unreachable: {e}")
        raise
    assert isinstance(out, str) and out
