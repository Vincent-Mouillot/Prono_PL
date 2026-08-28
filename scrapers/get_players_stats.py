# scrapers/get_players_match_stats.py
import sqlite3, time
import pandas as pd
from understatapi import UnderstatClient
from database.get_cloud_db import DB_PATH

# À ajuster après inspection
FIELDS = ["player_id", "player", "team_id", "position", "time", "goals",
          "xG", "assists", "xA", "shots", "key_passes",
          "xGChain", "xGBuildup", "yellow_card", "red_card"]


def roster_to_df(roster: dict, match_id: str) -> pd.DataFrame:
    rows = []
    for side in ("h", "a"):
        for entry in roster.get(side, {}).values():
            row = {f: entry.get(f) for f in FIELDS}
            row["id_match"], row["h_a"] = match_id, side
            rows.append(row)
    return pd.DataFrame(rows)


def pending_match_ids(con, limit: int | None = None) -> list[str]:
    """Matchs joués dont le roster n'est pas encore en base."""
    df = pd.read_sql_query("""
        SELECT g.id FROM games g
        LEFT JOIN players_match_stats p ON p.id_match = g.id
        WHERE g.goals_h IS NOT NULL AND p.id_match IS NULL
        GROUP BY g.id ORDER BY g.datetime
    """, con)
    return df["id"].tolist()[:limit]


def get_players_match_stats(limit: int | None = None, delay: float = 1.0):
    con = sqlite3.connect(DB_PATH)
    pending = pending_match_ids(con, limit)
    dates = pd.read_sql_query("SELECT id, datetime FROM games;", con)

    frames = []
    with UnderstatClient() as understat:
        for i, match_id in enumerate(pending, 1):
            try:
                frames.append(roster_to_df(
                    understat.match(match=match_id).get_roster_data(), match_id))
            except Exception as e:
                print(f"{match_id} — skipped: {e}")
            time.sleep(delay)
            if i % 50 == 0:
                print(f"{i}/{len(pending)}")

    if not frames:
        print("Rien à insérer")
        con.close()
        return

    df = pd.concat(frames, ignore_index=True).merge(
        dates.rename(columns={"id": "id_match", "datetime": "date"}), on="id_match")
    df = df.rename(columns={"player_id": "id_player", "team_id": "id_team"})

    cols = list(df.columns)
    con.executemany(
        f"INSERT OR REPLACE INTO players_match_stats ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        df.itertuples(index=False, name=None))
    con.commit()
    con.close()
    print(f"{len(df)} lignes ({len(frames)} matchs)")

if __name__ == "__main__":
    get_players_match_stats()