# streamlit cheatsheet

## Run

```sh
uv add streamlit
uv run streamlit run app.py
uv run streamlit run app.py --server.headless true --server.port 8501
```

## Minimal app

```python
# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="my-dashboard", layout="wide")
st.title("My dashboard")

@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv("data.csv")

df = load()
st.dataframe(df)

name = st.text_input("Filter by name")
if name:
    st.dataframe(df[df["name"].str.contains(name, case=False)])

st.line_chart(df.set_index("date")["value"])
```

## Session state

```python
if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("Increment"):
    st.session_state.count += 1

st.write(st.session_state.count)
```

## Cache: data vs resource

```python
@st.cache_data
def transform(df): ...        # pure, hashable in/out

@st.cache_resource
def db_engine():               # expensive, shared, not hashable
    return create_engine(URL)
```

## Multi-page

```
app.py
pages/
  1_📊_Overview.py
  2_🔍_Search.py
```

## Docker

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.14-alpine
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.headless=true", "--server.port=8501", "--server.address=0.0.0.0"]
```
