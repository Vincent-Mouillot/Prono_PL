import sqlite3
import pandas as pd


def insert_initial_ranking(con: sqlite3.Connection, df: pd.DataFrame, season: str) -> None:
    """Insert initial ranking for a season if it doesn't already exist."""
    existing = pd.read_sql_query("SELECT season FROM initial_ranking;", con)["season"].tolist()

    if season not in existing:
        df.to_sql("initial_ranking", con, if_exists="append", index=False)
        print(f"Initial ranking {season} inserted")
    else:
        print(f"Initial ranking {season} already exists, skipping")


# ── All seasons ───────────────────────────────────────────────────────────────
# Add new seasons below following the same pattern

ALL_SEASONS = {
    2025: pd.DataFrame([
        {"season": 2025, "title": "Liverpool",               "rank": 1},
        {"season": 2025, "title": "Arsenal",                 "rank": 2},
        {"season": 2025, "title": "Manchester City",         "rank": 3},
        {"season": 2025, "title": "Chelsea",                 "rank": 4},
        {"season": 2025, "title": "Newcastle United",        "rank": 5},
        {"season": 2025, "title": "Aston Villa",             "rank": 6},
        {"season": 2025, "title": "Nottingham Forest",       "rank": 7},
        {"season": 2025, "title": "Brighton",                "rank": 8},
        {"season": 2025, "title": "Bournemouth",             "rank": 9},
        {"season": 2025, "title": "Brentford",               "rank": 10},
        {"season": 2025, "title": "Fulham",                  "rank": 11},
        {"season": 2025, "title": "Crystal Palace",          "rank": 12},
        {"season": 2025, "title": "Everton",                 "rank": 13},
        {"season": 2025, "title": "West Ham United",         "rank": 14},
        {"season": 2025, "title": "Manchester United",       "rank": 15},
        {"season": 2025, "title": "Wolverhampton Wanderers", "rank": 16},
        {"season": 2025, "title": "Tottenham",               "rank": 17},
        # Promoted from Championship
        {"season": 2025, "title": "Leeds United",            "rank": 18},
        {"season": 2025, "title": "Burnley",                 "rank": 19},
        {"season": 2025, "title": "Sunderland",              "rank": 20},
    ]),
}
