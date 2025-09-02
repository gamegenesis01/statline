from __future__ import annotations
import requests
from typing import Iterator, Dict, Any

MLB_BASE = "https://statsapi.mlb.com/api/v1"

def iter_season_game_ids(season: int) -> Iterator[int]:
    params = {"sportId": 1, "season": season}
    r = requests.get(f"{MLB_BASE}/schedule", params=params)
    r.raise_for_status()
    data = r.json()
    for date in data.get("dates", []):
        for g in date.get("games", []):
            if g.get("gamePk"):
                yield int(g["gamePk"])

def get_boxscore(game_pk: int) -> Dict[str, Any]:
    r = requests.get(f"{MLB_BASE}/game/{game_pk}/boxscore")
    r.raise_for_status()
    return r.json()

def get_game_feed(game_pk: int) -> Dict[str, Any]:
    r = requests.get(f"{MLB_BASE}/game/{game_pk}/feed/live")
    r.raise_for_status()
    return r.json()
