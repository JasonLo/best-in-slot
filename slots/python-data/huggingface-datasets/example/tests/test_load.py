from pathlib import Path

from hf_datasets_example import add_length_column, load_local_csv


def test_load_and_map(tmp_path: Path) -> None:
    csv = tmp_path / "tiny.csv"
    csv.write_text("text,label\nhello,0\nworld!,1\n")
    ds = load_local_csv(csv)
    assert ds.num_rows == 2
    out = add_length_column(ds)
    assert out["len"] == [5, 6]
