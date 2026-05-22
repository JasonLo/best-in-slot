import pandas as pd


def top_topics(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    return (
        df.groupby("topic", as_index=False)
        .agg(count=("id", "count"), avg_score=("score", "mean"))
        .sort_values("count", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
