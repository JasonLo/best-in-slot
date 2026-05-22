import altair as alt
import pandas as pd


def topic_bar(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("topic:N", sort="-y"),
            y="count:Q",
            tooltip=["topic", "count"],
        )
        .properties(width=400, height=240, title="topics")
    )
