from __future__ import annotations
import requests
from typing import Iterator, Dict, Any
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

NHL_BASE = "https://statsapi.web.nhl.com/api/v1"
_DEFAULT_TIMEOUT = 15  # seconds


def _session() -> requests.Session:
    """
    Build a Session with robust retries for transient network/DNS hiccups.
    """
    s = requests.Session()
    retry = Retry(
        total=5,                # total attempts
        connect=5,              # DNS/connect retries
        read=5,
        backoff_factor=0.8,     # exponential backoff: 0.8, 1.6, 3.2, ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({"User-Agent": "statline-core/nhl"})
    return s


_SESSION = _session()


def _get(path: str, params: dict | None = None) -> requests.Response:
    resp = _SESSION.get(f"{NHL_BASE}{path}", params=params or {}, timeout=_DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp


def iter_season_game_ids(season_str: str) -> Iterator[int]:
    """
    Yields gamePk for the NHL season (e.g., '20232024').
    Retries network issues automatically via the session.
    """
    r = _get("/schedule", params={"season": season_str})
    data = r.json()
    for d in data.get("dates", []):
        for g in d.get("games", []):
            game_pk = g.get("gamePk")
            if game_pk:
                yield int(game_pk)


def get_boxscore(game_pk: int) -> Dict[str, Any]:
    r = _get(f"/game/{game_pk}/boxscore")
    return r.json()
