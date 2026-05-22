# transformers cheatsheet

## Text generation

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

name = "sshleifer/tiny-gpt2"      # tiny; swap for real model
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name)

inputs = tok("Once upon a time,", return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=20, do_sample=False)
print(tok.decode(out[0], skip_special_tokens=True))
```

## Chat templates (instruction-tuned models)

```python
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "What is 2+2?"},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt").to(model.device)
out = model.generate(**inputs, max_new_tokens=64)
```

## Embeddings

```python
from transformers import AutoTokenizer, AutoModel
import torch

tok = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

texts = ["hello world", "how are you?"]
enc = tok(texts, padding=True, truncation=True, return_tensors="pt")
with torch.no_grad():
    out = model(**enc).last_hidden_state.mean(dim=1)   # mean-pooled
```

## Speech (audio)

```python
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
print(asr("audio.wav")["text"])
```

## Quantise for GPU memory

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype="bfloat16")
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization_config=bnb,
    device_map="auto",
)
```

## Pinning

```python
AutoModel.from_pretrained("org/model", revision="commit_sha_here")
```
