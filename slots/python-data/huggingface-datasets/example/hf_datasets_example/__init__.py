from pathlib import Path

from datasets import Dataset, load_dataset


def load_local_csv(path: str | Path) -> Dataset:
    """Load a single CSV as a HuggingFace Dataset."""
    return load_dataset("csv", data_files=str(path), split="train")


def add_length_column(ds: Dataset, text_col: str = "text") -> Dataset:
    return ds.map(lambda r: {"len": len(r[text_col])})
