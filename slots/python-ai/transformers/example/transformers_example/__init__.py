from functools import cache

from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "sshleifer/tiny-gpt2"  # ~5 MB; safe for CI smoke tests


@cache
def load():
    tok = AutoTokenizer.from_pretrained(MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(MODEL)
    return tok, model


def generate(prompt: str, max_new_tokens: int = 8) -> str:
    tok, model = load()
    inputs = tok(prompt, return_tensors="pt")
    out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0], skip_special_tokens=True)
