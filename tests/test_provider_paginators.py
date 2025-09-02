from statline.providers import nba_balldontlie as nba, mlb_statsapi as mlb, nhl_statsapi as nhl

class Dummy:
    def __init__(self, data): self._data=data
    def raise_for_status(self): pass
    def json(self): return self._data

def test_nba_paginate(monkeypatch):
    pages = [
        {"data": [{"id": 1}], "meta": {"total_pages": 2}},
        {"data": [{"id": 2}], "meta": {"total_pages": 2}},
    ]
    calls = {"i": 0}
    def fake_get(url, params=None):
        i = calls["i"]; calls["i"] += 1
        return Dummy(pages[i])
    monkeypatch.setattr(nba.requests, "get", fake_get)
    out = list(nba._paginate("games", {}))
    assert [o["id"] for o in out] == [1,2]

def test_mlb_iter_ids(monkeypatch):
    data = {"dates":[{"games":[{"gamePk":111},{"gamePk":222}]}]}
    monkeypatch.setattr(mlb.requests, "get", lambda *a, **k: Dummy(data))
    assert list(mlb.iter_season_game_ids(2025)) == [111,222]

def test_nhl_iter_ids(monkeypatch):
    data = {"dates":[{"games":[{"gamePk":333},{"gamePk":444}]}]}
    monkeypatch.setattr(nhl.requests, "get", lambda *a, **k: Dummy(data))
    assert list(nhl.iter_season_game_ids("20242025")) == [333,444]
