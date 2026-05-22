import pandas as pd

from pandas_example import top_topics


def test_returns_top_n_in_order() -> None:
    df = pd.DataFrame(
        {
            "id": range(7),
            "topic": ["a", "a", "a", "b", "b", "c", "c"],
            "score": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        }
    )
    out = top_topics(df, n=2)
    assert list(out["topic"]) == ["a", "b"]
    assert list(out["count"]) == [3, 2]
    assert out.loc[out["topic"] == "a", "avg_score"].iloc[0] == 2.0
