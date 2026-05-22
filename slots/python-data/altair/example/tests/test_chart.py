import altair as alt
import pandas as pd

from altair_example import topic_bar


def test_chart_serialises_to_dict() -> None:
    df = pd.DataFrame({"topic": ["a", "b", "c"], "count": [3, 1, 2]})
    chart = topic_bar(df)
    spec = chart.to_dict()
    assert spec["mark"]["type"] == "bar"
    assert spec["encoding"]["x"]["field"] == "topic"
    assert spec["encoding"]["y"]["field"] == "count"
    assert isinstance(chart, alt.Chart)
