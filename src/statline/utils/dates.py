from __future__ import annotations
from datetime import datetime, timedelta, timezone

def two_year_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=730)
    return (start, now)

def last_two_seasons_nba(now: datetime) -> list[int]:
    if now.month >= 10:
        cur = now.year
    else:
        cur = now.year - 1
    return [cur - 1, cur]

def last_two_seasons_mlb(now: datetime) -> list[int]:
    return [now.year - 1, now.year]

def last_two_seasons_nhl(now: datetime) -> list[str]:
    if now.month >= 10:
        start = now.year
    else:
        start = now.year - 1
    return [f"{start-1}{start}", f"{start}{start+1}"]
