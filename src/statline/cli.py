from __future__ import annotations
import typer
from datetime import datetime, timezone
from typing import List
from .etl.ingest import backfill_nba, bootstrap
from .etl.ingest_mlb import backfill_mlb
from .etl.ingest_nhl import backfill_nhl
from .features.rolling import last_n_avg_pts
from .utils.dates import last_two_seasons_nba, last_two_seasons_mlb, last_two_seasons_nhl

app = typer.Typer(help="StatLine Core CLI")

@app.command()
def initdb():
    "Create database tables."
    bootstrap()
    typer.secho("Database initialized.", fg=typer.colors.GREEN)

@app.command()
def ingest(league: str = typer.Argument(..., help="League code e.g. NBA/MLB/NHL"),
           seasons: List[str] = typer.Option(None, help="NBA/MLB: 2024 2025, NHL: 20232024 20242025")):
    "Backfill data for the given league and seasons."
    L = league.upper()
    if L == "NBA":
        if not seasons: typer.echo("Provide --seasons like 2024 2025"); raise typer.Exit(1)
        backfill_nba([int(s) for s in seasons])
    elif L == "MLB":
        if not seasons: typer.echo("Provide --seasons like 2024 2025"); raise typer.Exit(1)
        backfill_mlb([int(s) for s in seasons])
    elif L == "NHL":
        if not seasons: typer.echo("Provide --seasons like 20232024 20242025"); raise typer.Exit(1)
        backfill_nhl([str(s) for s in seasons])
    else:
        typer.secho(f"League {league} not implemented.", fg=typer.colors.RED); raise typer.Exit(2)
    typer.secho(f"{L} backfill complete for seasons: {seasons}", fg=typer.colors.GREEN)

@app.command()
def ingest_two_years():
    "Detect last ~2 seasons per league and backfill all."
    now = datetime.now(timezone.utc)
    nba_seasons = last_two_seasons_nba(now)
    mlb_seasons = last_two_seasons_mlb(now)
    nhl_seasons = last_two_seasons_nhl(now)
    typer.secho(f"NBA seasons: {nba_seasons}")
    backfill_nba(nba_seasons)
    typer.secho(f"MLB seasons: {mlb_seasons}")
    backfill_mlb(mlb_seasons)
    typer.secho(f"NHL seasons: {nhl_seasons}")
    backfill_nhl(nhl_seasons)
    typer.secho("All leagues backfilled for ~2 years.", fg=typer.colors.GREEN)

@app.command()
def features(league: str, target: str = "pts", window: int = 10):
    "Build rolling features for the specified market (baseline)."
    if league.upper() != "NBA" or target != "pts":
        typer.secho("Only NBA pts baseline rolling feature is shown here.", fg=typer.colors.YELLOW)
    df = last_n_avg_pts(window)
    typer.echo(df.head().to_string(index=False))

if __name__ == "__main__":
    app()
