# huggingface datasets cheatsheet

## Load from the Hub

```python
from datasets import load_dataset

ds = load_dataset("imdb", split="train[:1%]")
print(ds)                          # Dataset({features: ['text', 'label'], num_rows: 250})
print(ds[0])
```

## Load local files

```python
ds = load_dataset("csv", data_files="data/*.csv")
ds = load_dataset("parquet", data_files={"train": "train.parquet", "test": "test.parquet"})
ds = load_dataset("json", data_files="data.jsonl")
```

## Streaming (no download)

```python
ds = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True)
for row in ds.take(10):
    print(row["text"][:100])
```

## With pytorch

```python
ds_t = ds.with_format("torch", columns=["input_ids", "label"])
loader = torch.utils.data.DataLoader(ds_t, batch_size=32, shuffle=True)
```

## Map / filter (cached)

```python
def tokenize(batch):
    return {"len": [len(t) for t in batch["text"]]}

ds = ds.map(tokenize, batched=True)
ds = ds.filter(lambda r: r["len"] > 50)
```

## Save / load locally

```python
ds.save_to_disk("./my-dataset")
from datasets import load_from_disk
ds = load_from_disk("./my-dataset")
```

## Push (private)

```sh
huggingface-cli login
```

```python
ds.push_to_hub("jasonlo/my-dataset", private=True)
```
