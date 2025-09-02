from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine
from ..models import Base, League, Team, Player, Game, PlayerGameStat
from ..providers import nhl_statsapi as nhl


def backfill_nhl(seasons: list[str]):
    """
    Backfill NHL data for the given list of seasons (e.g., ['20232024', '20242025']).
    Uses provider-level retries and skips gracefully on per-game errors.
    """
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        league = _get_or_create_league(s, code="NHL", name="National Hockey League")

        for season in seasons:
            try:
                game_ids = list(nhl.iter_season_game_ids(season))
            except Exception as e:
                print(f"⚠️ Unable to list NHL schedule for season {season}: {e}")
                continue

            for game_pk in game_ids:
                try:
                    box = nhl.get_boxscore(game_pk)
                except Exception as e:
                    print(f"⚠️ Skipping NHL game {game_pk}: {e}")
                    continue

                teams = box.get("teams", {})
                home = teams.get("home", {})
                away = teams.get("away", {})
                home_team_info = home.get("team") or {}
                away_team_info = away.get("team") or {}

                home_team = _get_or_create_team(
                    s, league.id, str(home_team_info.get("id") or f"home-{game_pk}"),
                    home_team_info.get("name") or "HOME"
                )
                away_team = _get_or_create_team(
                    s, league.id, str(away_team_info.get("id") or f"away-{game_pk}"),
                    away_team_info.get("name") or "AWAY"
                )

                # Use season start of Oct 1 as a placeholder date if exact isn't handy.
                date = datetime.strptime(season[:4] + "-10-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
                game = _get_or_create_game(
                    s, league.id, str(game_pk), int(season[:4]), date,
                    home_team.id, away_team.id, status="Final"
                )

                for side_key in ("home", "away"):
                    skaters = (teams.get(side_key, {}).get("skaters") or [])
                    players_dict = teams.get(side_key, {}).get("players") or {}
                    for sk_id in skaters:
                        pdata = players_dict.get(f"ID{sk_id}") or {}
                        person = pdata.get("person", {})
                        p_ext = str(person.get("id") or "")
                        if not p_ext:
                            continue
                        full = person.get("fullName") or ""
                        parts = full.split(" ")
                        first = parts[0] if parts else ""
                        last = " ".join(parts[1:]) if len(parts) > 1 else ""
                        player = _get_or_create_player(
                            s, league.id, p_ext, first, last or None, position=None,
                            team_id=home_team.id if side_key == "home" else away_team.id
                        )

                        skstats = pdata.get("stats", {}).get("skaterStats") or {}
                        goals = skstats.get("goals") or 0
                        assists = skstats.get("assists") or 0
                        proxy_pts = float(goals + assists)
                        _upsert_stat(s, league.id, game.id, player.id, pts=proxy_pts)

                s.commit()


# --------------------------
# Helper functions
# --------------------------

def _get_or_create_league(s: Session, code: str, name: str) -> League:
    league = s.query(League).filter_by(code=code).one_or_none()
    if not league:
        league = League(code=code, name=name)
        s.add(league)
        s.commit()
    return league


def _get_or_create_team(s: Session, league_id: int, ext_id: str, name: str) -> Team:
    t = s.query(Team).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not t:
        t = Team(league_id=league_id, ext_id=ext_id, name=name, abbreviation=None)
        s.add(t)
        s.flush()
    return t


def _get_or_create_player(
    s: Session,
    league_id: int,
    ext_id: str,
    first: str,
    last: str | None,
    position: str | None,
    team_id: int | None,
) -> Player:
    p = s.query(Player).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not p:
        p = Player(
            league_id=league_id,
            ext_id=ext_id,
            first_name=first,
            last_name=last or "",
            position=position,
            team_id=team_id,
        )
        s.add(p)
        s.flush()
    return p


def _get_or_create_game(
    s: Session,
    league_id: int,
    ext_id: str,
    season: int,
    date: datetime,
    home_team_id: int,
    visitor_team_id: int,
    status: str,
) -> Game:
    g = s.query(Game).filter_by(league_id=league_id, ext_id=ext_id).one_or_none()
    if not g:
        g = Game(
            league_id=league_id,
            ext_id=ext_id,
            season=season,
            date=date,
            home_team_id=home_team_id,
            visitor_team_id=visitor_team_id,
            status=status,
        )
        s.add(g)
        s.flush()
    return g


def _upsert_stat(s: Session, league_id: int, game_id: int, player_id: int, pts: float | None):
    exists = (
        s.query(PlayerGameStat)
        .filter_by(league_id=league_id, game_id=game_id, player_id=player_id)
        .one_or_none()
    )
    if not exists:
        s.add(
            PlayerGameStat(
                league_id=league_id,
                game_id=game_id,
                player_id=player_id,
                pts=pts,
            )
        )
