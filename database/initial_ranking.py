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
# Final standings of previous season = initial ranking for current season
# Team names match Understat naming convention

ALL_SEASONS = {
    # 2026-27 promoted: Coventry City, Ipswich, Hull City
    # 2025-26 final standings used as initial ranking
    2026: pd.DataFrame([
        {"season": 2026, "title": "Arsenal",                 "rank": 1},
        {"season": 2026, "title": "Manchester City",         "rank": 2},
        {"season": 2026, "title": "Manchester United",       "rank": 3},
        {"season": 2026, "title": "Aston Villa",             "rank": 4},
        {"season": 2026, "title": "Liverpool",               "rank": 5},
        {"season": 2026, "title": "Bournemouth",             "rank": 6},
        {"season": 2026, "title": "Sunderland",              "rank": 7},
        {"season": 2026, "title": "Brighton",                "rank": 8},
        {"season": 2026, "title": "Brentford",               "rank": 9},
        {"season": 2026, "title": "Chelsea",                 "rank": 10},
        {"season": 2026, "title": "Fulham",                  "rank": 11},
        {"season": 2026, "title": "Newcastle United",        "rank": 12},
        {"season": 2026, "title": "Everton",                 "rank": 13},
        {"season": 2026, "title": "Leeds",                   "rank": 14},
        {"season": 2026, "title": "Crystal Palace",          "rank": 15},
        {"season": 2026, "title": "Nottingham Forest",       "rank": 16},
        {"season": 2026, "title": "Tottenham",               "rank": 17},
        {"season": 2026, "title": "Coventry City",           "rank": 18},  # promoted
        {"season": 2026, "title": "Ipswich",                 "rank": 19},  # promoted
        {"season": 2026, "title": "Hull City",               "rank": 20},  # promoted
    ]),

    # 2024-25 promoted: Leeds, Burnley, Sunderland
    # 2023-24 final standings used as initial ranking
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
        {"season": 2025, "title": "West Ham",                "rank": 14},
        {"season": 2025, "title": "Manchester United",       "rank": 15},
        {"season": 2025, "title": "Wolverhampton Wanderers", "rank": 16},
        {"season": 2025, "title": "Tottenham",               "rank": 17},
        {"season": 2025, "title": "Leeds",                   "rank": 18},  # promoted
        {"season": 2025, "title": "Burnley",                 "rank": 19},  # promoted
        {"season": 2025, "title": "Sunderland",              "rank": 20},  # promoted
    ]),

    # 2023-24 promoted: Leicester, Ipswich, Southampton
    # 2022-23 final standings used as initial ranking
    2024: pd.DataFrame([
        {"season": 2024, "title": "Manchester City",         "rank": 1},
        {"season": 2024, "title": "Arsenal",                 "rank": 2},
        {"season": 2024, "title": "Liverpool",               "rank": 3},
        {"season": 2024, "title": "Aston Villa",             "rank": 4},
        {"season": 2024, "title": "Tottenham",               "rank": 5},
        {"season": 2024, "title": "Chelsea",                 "rank": 6},
        {"season": 2024, "title": "Newcastle United",        "rank": 7},
        {"season": 2024, "title": "Manchester United",       "rank": 8},
        {"season": 2024, "title": "West Ham",                "rank": 9},
        {"season": 2024, "title": "Crystal Palace",          "rank": 10},
        {"season": 2024, "title": "Brighton",                "rank": 11},
        {"season": 2024, "title": "Bournemouth",             "rank": 12},
        {"season": 2024, "title": "Fulham",                  "rank": 13},
        {"season": 2024, "title": "Wolverhampton Wanderers", "rank": 14},
        {"season": 2024, "title": "Everton",                 "rank": 15},
        {"season": 2024, "title": "Brentford",               "rank": 16},
        {"season": 2024, "title": "Nottingham Forest",       "rank": 17},
        {"season": 2024, "title": "Leicester",               "rank": 18},  # promoted
        {"season": 2024, "title": "Ipswich",                 "rank": 19},  # promoted
        {"season": 2024, "title": "Southampton",             "rank": 20},  # promoted
    ]),

    # 2023-24 promoted: Burnley, Sheffield United, Luton
    # 2021-22 final standings used as initial ranking
    2023: pd.DataFrame([
        {"season": 2023, "title": "Manchester City",         "rank": 1},
        {"season": 2023, "title": "Liverpool",               "rank": 2},
        {"season": 2023, "title": "Chelsea",                 "rank": 3},
        {"season": 2023, "title": "Tottenham",               "rank": 4},
        {"season": 2023, "title": "Arsenal",                 "rank": 5},
        {"season": 2023, "title": "Manchester United",       "rank": 6},
        {"season": 2023, "title": "West Ham",                "rank": 7},
        {"season": 2023, "title": "Leicester",               "rank": 8},
        {"season": 2023, "title": "Brighton",                "rank": 9},
        {"season": 2023, "title": "Wolverhampton Wanderers", "rank": 10},
        {"season": 2023, "title": "Newcastle United",        "rank": 11},
        {"season": 2023, "title": "Crystal Palace",          "rank": 12},
        {"season": 2023, "title": "Brentford",               "rank": 13},
        {"season": 2023, "title": "Aston Villa",             "rank": 14},
        {"season": 2023, "title": "Southampton",             "rank": 15},
        {"season": 2023, "title": "Everton",                 "rank": 16},
        {"season": 2023, "title": "Leeds",                   "rank": 17},
        {"season": 2023, "title": "Burnley",                 "rank": 18},  # promoted
        {"season": 2023, "title": "Sheffield United",        "rank": 19},  # promoted
        {"season": 2023, "title": "Luton",                   "rank": 20},  # promoted
    ]),

    # 2022-23 promoted: Fulham, Bournemouth, Nottingham Forest
    # 2020-21 final standings used as initial ranking
    2022: pd.DataFrame([
        {"season": 2022, "title": "Manchester City",         "rank": 1},
        {"season": 2022, "title": "Manchester United",       "rank": 2},
        {"season": 2022, "title": "Liverpool",               "rank": 3},
        {"season": 2022, "title": "Chelsea",                 "rank": 4},
        {"season": 2022, "title": "Leicester",               "rank": 5},
        {"season": 2022, "title": "West Ham",                "rank": 6},
        {"season": 2022, "title": "Tottenham",               "rank": 7},
        {"season": 2022, "title": "Arsenal",                 "rank": 8},
        {"season": 2022, "title": "Leeds",                   "rank": 9},
        {"season": 2022, "title": "Everton",                 "rank": 10},
        {"season": 2022, "title": "Aston Villa",             "rank": 11},
        {"season": 2022, "title": "Newcastle United",        "rank": 12},
        {"season": 2022, "title": "Wolverhampton Wanderers", "rank": 13},
        {"season": 2022, "title": "Crystal Palace",          "rank": 14},
        {"season": 2022, "title": "Southampton",             "rank": 15},
        {"season": 2022, "title": "Brighton",                "rank": 16},
        {"season": 2022, "title": "Burnley",                 "rank": 17},
        {"season": 2022, "title": "Fulham",                  "rank": 18},  # promoted
        {"season": 2022, "title": "Bournemouth",             "rank": 19},  # promoted
        {"season": 2022, "title": "Nottingham Forest",       "rank": 20},  # promoted
    ]),

    # 2021-22 promoted: Norwich, Watford, Brentford
    # 2019-20 final standings used as initial ranking
    2021: pd.DataFrame([
        {"season": 2021, "title": "Liverpool",               "rank": 1},
        {"season": 2021, "title": "Manchester City",         "rank": 2},
        {"season": 2021, "title": "Manchester United",       "rank": 3},
        {"season": 2021, "title": "Chelsea",                 "rank": 4},
        {"season": 2021, "title": "Leicester",               "rank": 5},
        {"season": 2021, "title": "Tottenham",               "rank": 6},
        {"season": 2021, "title": "Arsenal",                 "rank": 7},
        {"season": 2021, "title": "Leeds",                   "rank": 8},
        {"season": 2021, "title": "West Ham",                "rank": 9},
        {"season": 2021, "title": "Aston Villa",             "rank": 10},
        {"season": 2021, "title": "Newcastle United",        "rank": 11},
        {"season": 2021, "title": "Wolverhampton Wanderers", "rank": 12},
        {"season": 2021, "title": "Everton",                 "rank": 13},
        {"season": 2021, "title": "Crystal Palace",          "rank": 14},
        {"season": 2021, "title": "Southampton",             "rank": 15},
        {"season": 2021, "title": "Brighton",                "rank": 16},
        {"season": 2021, "title": "Burnley",                 "rank": 17},
        {"season": 2021, "title": "Norwich",                 "rank": 18},  # promoted
        {"season": 2021, "title": "Watford",                 "rank": 19},  # promoted
        {"season": 2021, "title": "Brentford",               "rank": 20},  # promoted
    ]),
}
