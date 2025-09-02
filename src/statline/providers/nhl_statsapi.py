from __future__ import annotations
import requests
from typing import Iterator, Dict, Any

NHL_BASE = "https://statsapi.web.nhl.com/api/v1"

def iter_season_game_ids(season_str: str) -> Iterator[int]:
    r = requests.get(f"{NHL_BASE}/schedule", params={"season": season_str})
    r.raise_for_status()
    data = r.json()
    for d in data.get("dates", []):
        for g in d.get("games", []):
            game_pk = g.get("gamePk")
            if game_pk:
                yield int(game_pk)

def get_boxscore(game_pk: int) -> Dict[str, Any]:
    r = requests.get(f"{NHL_BASE}/game/{game_pk}/boxscore")
    r.raise_for_status()
    return r.json()
