import pandas as pd
import streamlit as st

st.set_page_config(page_title="streamlit-example", layout="wide")
st.title("streamlit-example")


@st.cache_data
def load() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "day": list(range(1, 8)),
            "temp_c": [-5, -3, 0, 2, 6, 8, 10],
        }
    )


df = load()
st.dataframe(df, use_container_width=True)
st.line_chart(df.set_index("day")["temp_c"])

if "clicks" not in st.session_state:
    st.session_state.clicks = 0

if st.button("Click me"):
    st.session_state.clicks += 1

st.write(f"Clicked {st.session_state.clicks} times")
