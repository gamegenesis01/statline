for season in seasons:
    for game_pk in mlb.iter_season_game_ids(season):
        try:
            feed = mlb.get_game_feed(game_pk)
        except Exception as e:
            print(f"⚠️ Skipping game {game_pk}: {e}")
            continue

        game_data = feed.get("gameData", {})
        datetime_str = game_data.get("datetime", {}).get("dateTime")
        if not datetime_str:
            continue
        when = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))

        teams = game_data.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        home_ext = str(home.get("id"))
        away_ext = str(away.get("id"))
        home_team = _get_or_create_team(s, league.id, home_ext, home.get("name") or "HOME")
        away_team = _get_or_create_team(s, league.id, away_ext, away.get("name") or "AWAY")

        game = _get_or_create_game(
            s,
            league.id,
            str(game_pk),
            season,
            when,
            home_team.id,
            away_team.id,
            status=game_data.get("status", {}).get("detailedState", "Final"),
        )

        box = mlb.get_boxscore(game_pk)
        teams_bx = box.get("teams", {})
        for side in ("home", "away"):
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
                player = _get_or_create_player(
                    s,
                    league.id,
                    p_ext,
                    first,
                    last or None,
                    position=None,
                    team_id=home_team.id if side == "home" else away_team.id,
                )

                batting = (pdata.get("stats", {}) or {}).get("batting") or {}
                runs = batting.get("runs") or 0
                rbi = batting.get("rbi") or 0
                pts = float(runs + rbi)

                _upsert_stat(s, league.id, game.id, player.id, pts=pts)

        s.commit()
