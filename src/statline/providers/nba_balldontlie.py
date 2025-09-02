from __future__ import annotations
import time
from typing import Iterator
import requests

BASE = "https://api.balldontlie.io/v1"

def _paginate(endpoint: str, params: dict) -> Iterator[dict]:
    page = 1
    while True:
        resp = requests.get(f"{BASE}/{endpoint}", params={**params, "page": page, "per_page": 100})
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            yield item
        meta = data.get("meta", {})
        total_pages = meta.get("total_pages") or 1
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.2)

def iter_season_games(season: int) -> Iterator[dict]:
    yield from _paginate("games", {"seasons[]": season})

def get_game_stats(game_id: int) -> list[dict]:
    return list(_paginate("stats", {"game_ids[]": game_id}))

def iter_players() -> Iterator[dict]:
    yield from _paginate("players", {})

def iter_teams() -> Iterator[dict]:
    yield from _paginate("teams", {})
