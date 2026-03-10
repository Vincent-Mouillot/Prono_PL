import sqlite3
import pandas as pd
from pathlib import Path
from understatapi import UnderstatClient

# ── Config ────────────────────────────────────────────────────────────────────

root = Path(__file__).resolve().parent
while not (root / "Prono_PL").exists() and root != root.parent:
    root = root.parent

if not (root / "Prono_PL").exists():
    raise FileNotFoundError("Could not find 'Prono_PL' directory in any parent folder")

DB_PATH = root / "Prono_PL" / "understats_database.db"

# ── Fetch data ────────────────────────────────────────────────────────────────

understat = UnderstatClient()

player_data = understat.league(league="EPL").get_player_data(season="2025")

# ── Transform ─────────────────────────────────────────────────────────────────

def player_to_df(player: dict) -> pd.DataFrame:
    return pd.DataFrame([{
        'id':           player['id'],
        'player_name':  player['player_name'],
        'games':        player['games'],
        'time':         player['time'],
        'goals':        player['goals'],
        'xG':           player['xG'],
        'assists':      player['assists'],
        'xA':           player['xA'],
        'shots':        player['shots'],
        'key_passes':   player['key_passes'],
        'yellow_cards': player['yellow_cards'],
        'red_cards':    player['red_cards'],
        'position':     player['position'],
        'team_title':   player['team_title'],
        'npg':          player['npg'],
        'npxG':         player['npxG'],
        'xGChain':      player['xGChain'],
        'xGBuildup':    player['xGBuildup'],
    }])

def players_to_df(players: list[dict]) -> pd.DataFrame:
    return pd.concat([player_to_df(m) for m in players], ignore_index=True)

df = players_to_df(player_data)

# ── Append new rows to DB (based on PK) ──────────────────────────────────────

con = sqlite3.connect(DB_PATH)

existing_ids = pd.read_sql_query("SELECT id FROM players_stats;", con)["id"].tolist()

new_rows = df[~df["id"].isin(existing_ids)]

if new_rows.empty:
    print("No new rows to insert")
else:
    new_rows.to_sql("players_stats", con, if_exists="append", index=False)
    print(f"{len(new_rows)} new rows inserted")

con.close()