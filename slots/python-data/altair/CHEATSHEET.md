# altair cheatsheet

## Bar

```python
import altair as alt
import pandas as pd

df = pd.DataFrame({"topic": ["covid", "soil", "soybean"], "count": [120, 45, 80]})
bar = alt.Chart(df).mark_bar().encode(
    x=alt.X("topic:N", sort="-y"),
    y="count:Q",
    tooltip=["topic", "count"],
).properties(width=400, height=240)
```

## Time series

```python
df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=30, freq="D"),
                   "temp_c": range(-5, 25)})
line = alt.Chart(df).mark_line(point=True).encode(
    x="date:T",
    y="temp_c:Q",
)
```

## Scatter with color + size

```python
alt.Chart(df).mark_circle().encode(
    x="x:Q", y="y:Q",
    color="group:N",
    size="weight:Q",
    tooltip=["x", "y", "group"],
).interactive()                # pan/zoom
```

## Layered + faceted

```python
alt.layer(line, points).facet(column="group:N")
```

## Save

```python
chart.save("out.html")
chart.save("out.png", scale_factor=2)   # needs vl-convert-python
chart.save("out.json")
```

## In Streamlit

```python
import streamlit as st
st.altair_chart(bar, use_container_width=True)
```
