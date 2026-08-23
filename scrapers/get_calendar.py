import sqlite3
import pandas as pd
from understatapi import UnderstatClient
from database.get_cloud_db import DB_PATH


# ── Transform ─────────────────────────────────────────────────────────────────

def match_to_df(match: dict) -> pd.DataFrame:
    is_played = match['isResult']
    forecast = match.get('forecast')

    return pd.DataFrame([{
        'id':           match['id'],
        'datetime':     match['datetime'],
        'h_team':       match['h']['title'],
        'a_team':       match['a']['title'],
        'h_team_short': match['h']['short_title'],
        'a_team_short': match['a']['short_title'],
        'goals_h':      int(match['goals']['h']) if is_played else None,
        'goals_a':      int(match['goals']['a']) if is_played else None,
        'xg_h':         float(match['xG']['h']) if is_played else None,
        'xg_a':         float(match['xG']['a']) if is_played else None,
        'proba_w':      round(float(forecast['w']) * 100) if forecast else None,
        'proba_d':      round(float(forecast['d']) * 100) if forecast else None,
        'proba_l':      round(float(forecast['l']) * 100) if forecast else None,
        'result':       ('H' if int(match['goals']['h']) > int(match['goals']['a'])
                         else 'A' if int(match['goals']['h']) < int(match['goals']['a'])
                         else 'D') if is_played else None
    }])


def matches_to_df(matches: list[dict]) -> pd.DataFrame:
    return pd.concat([match_to_df(m) for m in matches], ignore_index=True)


# ── Main function ─────────────────────────────────────────────────────────────

def get_calendar(season: str = "2025"):
    """Fetch EPL calendar from Understat and merge it into the games table."""

    understat = UnderstatClient()
    match_data = understat.league(league="EPL").get_match_data(season=season)

    df = matches_to_df(match_data)

    con = sqlite3.connect(DB_PATH)

    try:
        existing_df = pd.read_sql_query("SELECT * FROM games;", con)
    except Exception:
        # Table does not exist yet
        df.to_sql("games", con, if_exists="replace", index=False)
        print(f"{len(df)} rows written to new games table")
        con.close()
        return

    # Identify new rows
    new_rows = df[~df["id"].isin(existing_df["id"])]

    # Identify existing rows to update
    merged = df.merge(existing_df, on="id", how="inner", suffixes=("", "_old"))

    # Detect changes
    cols_to_compare = [col for col in df.columns if col != "id"]
    updated_rows = merged[
        (merged[cols_to_compare] != merged[[f"{col}_old" for col in cols_to_compare]].values).any(axis=1)
    ][df.columns]

    # Insert new rows
    if not new_rows.empty:
        new_rows.to_sql("games", con, if_exists="append", index=False)

    # Update modified existing rows
    if not updated_rows.empty:
        cursor = con.cursor()
        for _, row in updated_rows.iterrows():
            set_clause = ", ".join([f"{col} = ?" for col in cols_to_compare])
            values = [row[col] for col in cols_to_compare]
            values.append(row["id"])

            cursor.execute(
                f"UPDATE games SET {set_clause} WHERE id = ?",
                values
            )
        con.commit()

    print(f"{len(new_rows)} new rows inserted")
    print(f"{len(updated_rows)} rows updated")

    con.close()


if __name__ == "__main__":
    get_calendar()
