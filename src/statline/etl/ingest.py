from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine
from ..models import Base, League, Team, Player, Game, PlayerGameStat
from ..providers import nba_balldontlie as nba

def bootstrap():
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        nba_league = s.query(League).filter_by(code="NBA").one_or_none()
        if not nba_league:
            nba_league = League(code="NBA", name="National Basketball Association")
            s.add(nba_league); s.commit()

        existing_teams = {t.ext_id: t for t in s.query(Team).filter_by(league_id=nba_league.id).all()}
        for t in nba.iter_teams():
            ext_id = str(t["id"])
            if ext_id not in existing_teams:
                s.add(Team(league_id=nba_league.id, ext_id=ext_id, name=t["full_name"], abbreviation=t.get("abbreviation")))
        s.commit()

        existing_players = {p.ext_id: p for p in s.query(Player).filter_by(league_id=nba_league.id).all()}
        for p in nba.iter_players():
            ext_id = str(p["id"])
            if ext_id not in existing_players:
                s.add(Player(league_id=nba_league.id, ext_id=ext_id,
                             first_name=p.get("first_name") or "", last_name=p.get("last_name") or "",
                             position=p.get("position") or None, team_id=None))
        s.commit()

def backfill_nba(seasons: list[int]):
    bootstrap()
    with SessionLocal() as s:
        nba_league = s.query(League).filter_by(code="NBA").one()
        teams_by_ext = {t.ext_id: t for t in s.query(Team).filter_by(league_id=nba_league.id).all()}
        players_by_ext = {p.ext_id: p for p in s.query(Player).filter_by(league_id=nba_league.id).all()}

        for season in seasons:
            for g in nba.iter_season_games(season):
                game_ext = str(g["id"])
                game = s.query(Game).filter_by(league_id=nba_league.id, ext_id=game_ext).one_or_none()
                if not game:
                    home_ext = str(g["home_team"]["id"]); vis_ext = str(g["visitor_team"]["id"])
                    game = Game(
                        league_id=nba_league.id, ext_id=game_ext, season=int(g["season"]),
                        date=datetime.fromisoformat(g["date"].replace("Z","+00:00")),
                        home_team_id=teams_by_ext[home_ext].id, visitor_team_id=teams_by_ext[vis_ext].id,
                        status=g.get("status","Final"),
                    )
                    s.add(game); s.flush()

                stats = nba.get_game_stats(int(g["id"]))
                for stat in stats:
                    p = stat["player"]; p_ext = str(p["id"])
                    player = players_by_ext.get(p_ext)
                    if not player:
                        player = Player(league_id=nba_league.id, ext_id=p_ext,
                                        first_name=p.get("first_name") or "", last_name=p.get("last_name") or "",
                                        position=p.get("position") or None, team_id=None)
                        s.add(player); s.flush(); players_by_ext[p_ext] = player

                    exists = s.query(PlayerGameStat).filter_by(league_id=nba_league.id, game_id=game.id, player_id=player.id).one_or_none()
                    if not exists:
                        s.add(PlayerGameStat(
                            league_id=nba_league.id, game_id=game.id, player_id=player.id,
                            minutes=_to_float(stat.get("min")), pts=_to_float(stat.get("pts")),
                            reb=_to_float(stat.get("reb")), ast=_to_float(stat.get("ast")),
                            stl=_to_float(stat.get("stl")), blk=_to_float(stat.get("blk")),
                            fga=_to_float(stat.get("fga")), fgm=_to_float(stat.get("fgm")),
                            fg3a=_to_float(stat.get("fg3a")), fg3m=_to_float(stat.get("fg3m")),
                            fta=_to_float(stat.get("fta")), ftm=_to_float(stat.get("ftm")),
                            turnovers=_to_float(stat.get("turnover")),
                        ))
                s.commit()

def _to_float(v):
    try:
        if v is None: return None
        return float(v)
    except Exception:
        return None
