from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Index

class Base(DeclarativeBase):
    pass

class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # NBA, MLB, NHL
    name: Mapped[str] = mapped_column(String(80))

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    ext_id: Mapped[str] = mapped_column(String(32), index=True)  # provider id
    name: Mapped[str] = mapped_column(String(100))
    abbreviation: Mapped[Optional[str]] = mapped_column(String(10))
    __table_args__ = (UniqueConstraint("league_id", "ext_id", name="uq_team_league_ext"),)

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    ext_id: Mapped[str] = mapped_column(String(32), index=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    position: Mapped[Optional[str]] = mapped_column(String(10))
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), index=True)
    __table_args__ = (UniqueConstraint("league_id", "ext_id", name="uq_player_league_ext"),)

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    ext_id: Mapped[str] = mapped_column(String(32), index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    visitor_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="Final")
    __table_args__ = (
        UniqueConstraint("league_id", "ext_id", name="uq_game_league_ext"),
        Index("ix_games_league_date", "league_id", "date"),
    )

class PlayerGameStat(Base):
    __tablename__ = "player_game_stats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    minutes: Mapped[Optional[float]] = mapped_column(Float)
    pts: Mapped[Optional[float]] = mapped_column(Float)
    reb: Mapped[Optional[float]] = mapped_column(Float)
    ast: Mapped[Optional[float]] = mapped_column(Float)
    stl: Mapped[Optional[float]] = mapped_column(Float)
    blk: Mapped[Optional[float]] = mapped_column(Float)
    fga: Mapped[Optional[float]] = mapped_column(Float)
    fgm: Mapped[Optional[float]] = mapped_column(Float)
    fg3a: Mapped[Optional[float]] = mapped_column(Float)
    fg3m: Mapped[Optional[float]] = mapped_column(Float)
    fta: Mapped[Optional[float]] = mapped_column(Float)
    ftm: Mapped[Optional[float]] = mapped_column(Float)
    turnovers: Mapped[Optional[float]] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("league_id", "game_id", "player_id", name="uq_stat_game_player"),)

class PropLine(Base):
    __tablename__ = "prop_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    market: Mapped[str] = mapped_column(String(32))
    line: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
