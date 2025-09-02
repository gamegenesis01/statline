from __future__ import annotations
import pandas as pd
from ..db import SessionLocal
from ..models import PlayerGameStat, Game

def last_n_avg_pts(n: int) -> pd.DataFrame:
    with SessionLocal() as s:
        q = (
            s.query(PlayerGameStat.player_id, PlayerGameStat.game_id, PlayerGameStat.pts, Game.date)
            .join(Game, Game.id == PlayerGameStat.game_id)
            .order_by(PlayerGameStat.player_id, Game.date)
        )
        df = pd.DataFrame(q.all(), columns=["player_id","game_id","pts","date"]).dropna(subset=["pts"])  # type: ignore[call-arg]
    df = df.sort_values(["player_id","date"]).reset_index(drop=True)
    df["rolling_pts_avg"] = (
        df.groupby("player_id")["pts"].rolling(window=n, min_periods=max(1, n//2)).mean().reset_index(level=0, drop=True)
    )
    return df
