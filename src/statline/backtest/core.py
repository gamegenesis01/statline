from __future__ import annotations
import pandas as pd

def simple_over_under(df_features: pd.DataFrame, prop_lines: pd.DataFrame, threshold: float = 0.0) -> pd.DataFrame:
    df = df_features.merge(prop_lines, on=["player_id","game_id"], how="inner")
    df["edge"] = df["rolling_pts_avg"] - df["line"]
    df["pick"] = df["edge"].apply(lambda x: "OVER" if x > threshold else "UNDER")
    return df
