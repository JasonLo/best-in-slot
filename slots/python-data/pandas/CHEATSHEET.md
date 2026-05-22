# pandas cheatsheet

## Read / write

```python
import pandas as pd

df = pd.read_csv("data.csv", dtype={"id": "int64", "name": "string"}, parse_dates=["created_at"])
df.to_parquet("data.parquet")              # prefer parquet for storage
df = pd.read_parquet("data.parquet")
```

## Selection / filtering

```python
df.loc[df["active"], ["id", "name"]]
df.query("active and age >= 18")
df[df["name"].str.contains("jason", case=False, na=False)]
```

## Transform (chained)

```python
out = (
    df.assign(year=lambda d: d["date"].dt.year)
      .query("year >= 2024")
      .rename(columns={"name": "username"})
      .reset_index(drop=True)
)
```

## Group / aggregate

```python
df.groupby("topic", as_index=False).agg(n=("id", "count"), avg=("score", "mean"))
```

## Merge

```python
left.merge(right, on="user_id", how="left", indicator=True)
```

## Interop

```python
arrow = df.to_arrow()                       # pyarrow.Table
pl = polars.from_pandas(df)                 # if you switch to polars
import duckdb; duckdb.from_df(df).query("SELECT name FROM df WHERE active")
```

## Plot via altair (preferred)

```python
import altair as alt
alt.Chart(df).mark_bar().encode(x="topic:N", y="count():Q")
```
