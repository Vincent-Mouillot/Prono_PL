import sqlite3
import pandas as pd
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

# Walk up from current file until we find the 'Prono_PL' directory
root = Path(__file__).resolve().parent
while not (root / "Prono_PL").exists() and root != root.parent:
    root = root.parent

if not (root / "Prono_PL").exists():
    raise FileNotFoundError("Could not find 'Prono_PL' directory in any parent folder")

DB_PATH = root / "Prono_PL" / "understats_database.db"

print(f"Database path: {DB_PATH}")

# ── Connection ────────────────────────────────────────────────────────────────

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
print("Connection OK")

# ── Create tables ─────────────────────────────────────────────────────────────

cur.executescript("""
CREATE TABLE IF NOT EXISTS teams_stats (
    id                TEXT PRIMARY KEY,
    id_team           TEXT,
    title             TEXT,
    h_a               TEXT,
    xG                REAL,
    xGA               REAL,
    npxG              REAL,
    npxGA             REAL,
    ppda_att          INTEGER,
    ppda_def          INTEGER,
    ppda_allowed_att  INTEGER,
    ppda_allowed_def  INTEGER,
    deep              INTEGER,
    deep_allowed      INTEGER,
    scored            INTEGER,
    missed            INTEGER,
    xpts              REAL,
    result            TEXT,
    date              TEXT,
    wins              INTEGER,
    draws             INTEGER,
    loses             INTEGER,
    pts               INTEGER,
    npxGD             REAL
);

CREATE TABLE IF NOT EXISTS players_stats (
    id            TEXT PRIMARY KEY,
    player_name   TEXT,
    games         INTEGER,
    time          INTEGER,
    goals         INTEGER,
    xG            REAL,
    assists       INTEGER,
    xA            REAL,
    shots         INTEGER,
    key_passes    INTEGER,
    yellow_cards  INTEGER,
    red_cards     INTEGER,
    position      TEXT,
    team_title    TEXT,
    npg           INTEGER,
    npxG          REAL,
    xGChain       REAL,
    xGBuildup     REAL
);

CREATE TABLE IF NOT EXISTS games (
    id        TEXT PRIMARY KEY,
    datetime  TEXT,
    h_team    TEXT,
    a_team    TEXT,
    h_team_short    TEXT,
    a_team_short    TEXT,
    goals_h   INTEGER,
    goals_a   INTEGER,
    xg_h      REAL,
    xg_a      REAL,
    proba_w   INTEGER,
    proba_d   INTEGER,
    proba_l   INTEGER,
    result    TEXT
);

CREATE TABLE IF NOT EXISTS initial_ranking (
    season  INTEGER,
    title   TEXT,
    rank    INTEGER,
    PRIMARY KEY (season, title)
);
""")

con.commit()
print("Tables created successfully")

# ── Insert initial rankings ───────────────────────────────────────────────────
 
from initial_ranking import insert_initial_ranking, ALL_SEASONS
 
for season, df in ALL_SEASONS.items():
    insert_initial_ranking(con, df, season)
 

# ── Check ─────────────────────────────────────────────────────────────────────

tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
    con
)
print("\nExisting tables:")
print(tables.to_string(index=False))

for table in tables['name']:
    info = pd.read_sql_query(f"PRAGMA table_info({table});", con)
    print(f"\n── {table} ({len(info)} columns) ──")
    print(info[['name', 'type', 'notnull', 'pk']].to_string(index=False))

# ── Close ─────────────────────────────────────────────────────────────────────

con.close()
print("\nConnection closed — database initialized ✓")
