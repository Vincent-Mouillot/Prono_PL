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

match_data = understat.league(league="EPL").get_match_data(season="2025")

# ── Transform ─────────────────────────────────────────────────────────────────

def match_to_df(match: dict) -> pd.DataFrame:
    is_played = match['isResult']
    forecast = match.get('forecast')

    return pd.DataFrame([{
        'id':       match['id'],
        'datetime': match['datetime'],
        'h_team':   match['h']['short_title'],
        'a_team':   match['a']['short_title'],
        'goals_h':  int(match['goals']['h']) if is_played else None,
        'goals_a':  int(match['goals']['a']) if is_played else None,
        'xg_h':     float(match['xG']['h']) if is_played else None,
        'xg_a':     float(match['xG']['a']) if is_played else None,
        'proba_w':  round(float(forecast['w']) * 100) if forecast else None,
        'proba_d':  round(float(forecast['d']) * 100) if forecast else None,
        'proba_l':  round(float(forecast['l']) * 100) if forecast else None,
        'result':   ('H' if int(match['goals']['h']) > int(match['goals']['a'])
                     else 'A' if int(match['goals']['h']) < int(match['goals']['a'])
                     else 'D') if is_played else None
    }])

# Pour une liste de matchs
def matches_to_df(matches: list[dict]) -> pd.DataFrame:
    return pd.concat([match_to_df(m) for m in matches], ignore_index=True)

df = matches_to_df(match_data)

# ── Append new rows to DB (based on PK) ──────────────────────────────────────

con = sqlite3.connect(DB_PATH)

df.to_sql("games", con, if_exists="replace", index=False)
print(f"{len(df)} rows written")

con.close()