# altair

**Slot**: Declarative interactive plots (matches `code-template` default).

## Why altair

Grammar-of-graphics on top of Vega-Lite. Plots are JSON objects — easy to serialise, embed in Streamlit / Jupyter / Astro, version-control. Plays well with pandas; no figure-state nonsense.

## Conventions

- One chart = one `alt.Chart(df)` call followed by `.mark_*()` and `.encode(...)`.
- Encoding short-hand: `"colName:Q"` (quantitative), `"colName:N"` (nominal), `"colName:O"` (ordinal), `"colName:T"` (temporal). Use it — it's faster than long-form.
- For dashboards in Streamlit: `st.altair_chart(chart, use_container_width=True)`.
- For static export to PNG/SVG/PDF: `chart.save("out.png", scale_factor=2)` (requires `vl-convert-python`).
- Keep DataFrames < ~5k rows; above that, sample or aggregate before charting (Vega-Lite renders client-side).

## Alternatives considered

- **matplotlib** — fine for one-shot static plots, awful for interactive / dashboards. Use only when altair can't express it (rare).
- **plotly** — heavier JS payload; use when you need 3D or specific traces altair lacks.
- **seaborn** — built on matplotlib; same trade-offs.

## Gotchas

- `max_rows=5000` default — raise with `alt.data_transformers.disable_max_rows()` only if you know what you're doing.
- Time columns must be actual datetimes (`pd.to_datetime(...)`); strings get treated as nominal and sort wrong.
- For Streamlit's auto-theming, prefer `alt.Theme.config(...)` over per-chart styling.
