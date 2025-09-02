from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine
from ..models import Base, League, Team, Player, Game, PlayerGameStat
from ..providers import mlb_statsapi as mlb

def backfill_mlb(seasons: list[int]):
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        league = _get_or_create_league(s, code="MLB", name="Major League Baseball")

        for season in seasons:
            for game_pk in mlb.iter_season_game_ids(season):
                feed = mlb.get_game_feed(game_pk)
                game_data = feed.get("gameData", {})
                datetime_str = game_data.get("datetime",{}).get("dateTime")
                if not datetime_str:
                    continue
                when = datetime.fromisoformat(datetime_str.replace("Z","+00:00"))

                teams = game_data.get("teams", {})
                home = teams.get("home", {}); away = teams.get("away", {})

                home_ext = str(home.get("id")); away_ext = str(away.get("id"))
                home_team = _get_or_create_team(s, league.id, home_ext, home.get("name") or "HOME")
                away_team = _get_or_create_team(s, league.id, away_ext, away.get("name") or "AWAY")

                game = _get_or_create_game(s, league.id, str(game_pk), season, when, home_team.id, away_team.id, status=game_data.get("status",{}).get("detailedState","Final"))

                box = mlb.get_boxscore(game_pk)
                teams_bx = box.get("teams", {})
                for side in ("home","away"):
                    t = teams_bx.get(side, {})
                    players = t.get("players", {}) or {}
                    for pid, pdata in players.items():
                        person = pdata.get("person", {})
                        p_ext = str(person.get("id") or "")
                        if not p_ext:
                            continue
                        full = person.get("fullName") or ""
                        parts = full.split(" ")
                        first = parts[0] if parts else ""
                        last = " ".join(parts[1:]) if len(parts) > 1 else ""
                        player = _get_or_create_player(s, league.id, p_ext, first, last or None, position=None, team_id=home_team.id if side=="home" else away_team.id)

                        batting = (pdata.get("stats", {}) or {}).get("batting") or {}
                        runs = batting.get("runs") or 0
                        rbi = batting.get("rbi") or 0
                        pts = float(runs + rbi)

                        _upsert_stat(s, league.id, game.id, player.id, pts=pts)

                s.commit()

def _get_or_create_league(s: Session, code: str, name: str) -> League:
    league = s.query(League).filter_by(code=code).one_or_none()
    if not league:
        league = League(code=code, name=name)
        s.add(league); s.commit()
    return league

def _get_or_create_team(s: Session, league_id: int, ext_id: str, name: str) -> Team:
    t = s.query(Team).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not t:
        t = Team(league_id=league_id, ext_id=ext_id, name=name, abbreviation=None)
        s.add(t); s.flush()
    return t

def _get_or_create_player(s: Session, league_id: int, ext_id: str, first: str, last: str|None, position: str|None, team_id: int|None) -> Player:
    p = s.query(Player).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not p:
        p = Player(league_id=league_id, ext_id=ext_id, first_name=first, last_name=last or "", position=position, team_id=team_id)
        s.add(p); s.flush()
    return p

def _get_or_create_game(s: Session, league_id: int, ext_id: str, season: int, date: datetime, home_team_id: int, visitor_team_id: int, status: str) -> Game:
    g = s.query(Game).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not g:
        g = Game(league_id=league_id, ext_id=ext_id, season=season, date=date, home_team_id=home_team_id, visitor_team_id=visitor_team_id, status=status)
        s.add(g); s.flush()
    return g

def _upsert_stat(s: Session, league_id: int, game_id: int, player_id: int, pts: float|None):
    exists = s.query(PlayerGameStat).filter_by(league_id=league_id, game_id=game_id, player_id=player_id).one_or_none()
    if not exists:
        s.add(PlayerGameStat(league_id=league_id, game_id=game_id, player_id=player_id, pts=pts))
