# pandas

**Slot**: In-memory tabular data — ETL, analysis, glue between APIs and stores.

## Why pandas

Default for any rectangular data that fits in RAM. The ecosystem (pyarrow, duckdb, sklearn, plotnine, altair) all speak DataFrame fluently. Used across `code-template` (default dev dep), `pelican-data-loader`, dashboards.

## Conventions

- Always type-hint `pd.DataFrame` at function boundaries.
- Use `pd.read_csv("...", dtype={...})` — never let pandas infer types silently for production data.
- Prefer method chaining (`.assign().query().rename()`) over re-binding `df`.
- For >RAM datasets switch to `duckdb` (SQL) or `polars` (lazy) — both interop via `.to_arrow()` / `.from_arrow()`.
- Plot with [altair](../altair/), not `df.plot()`, for anything you'll share.

## Alternatives considered

- **polars** — faster, lazy, strict schemas. Worth learning; not yet the default in DSI/personal code.
- **duckdb** — when the operation is "SQL on a big file."
- **dask** — distributed pandas; only when you've outgrown a single machine (`pelican-data-loader` uses it).

## Gotchas

- `SettingWithCopyWarning` is a real bug 80% of the time — copy or use `.loc[…, col] =`.
- `df.merge` defaults to inner join — always pass `how=` explicitly.
- `pd.read_csv(parse_dates=[...])` is faster than parsing strings after the fact.
- Avoid `apply(lambda row: ...)` unless you really must — vectorise or use `np.where`.
