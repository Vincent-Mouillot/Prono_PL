import sqlite3
import pandas as pd

DB_NAME = "understats_database.db"

con = sqlite3.connect(DB_NAME)

games = pd.read_sql_query("SELECT * FROM teams_stats;", con)

def compute_standings(df_teams: pd.DataFrame) -> pd.DataFrame:
    """
    Compute standings snapshot after each matchday.
    Input: teams_stats df (one row per team per match)
    Output: long df with columns [matchday, team, points, cumulative_points, rank]
    """

    played = df_teams.dropna(subset=["result"]).copy()
    played["date"] = pd.to_datetime(played["date"])
    played = played.sort_values(["id_team", "date"])

    # Matchday = rank by date within each team
    played["matchday"] = played.groupby("id_team").cumcount() + 1

    played["points"] = played["result"].map({"w": 3, "d": 1, "l": 0})

    played["cumulative_points"] = played.groupby("id_team")["points"].cumsum()

    played["goal_difference"] = played["scored"] - played["missed"]

    played["cumulative_goal_difference"] = played.groupby("id_team")["goal_difference"].cumsum()

    played["sort_key"] = (
        played["cumulative_points"] * 1000 +
        played["cumulative_goal_difference"]
    )

    played["rank"] = played.groupby("matchday")["sort_key"].rank(
        ascending=False, method="min"
    ).astype(int)

    played = played.drop(columns="sort_key")

    return played[["matchday", "id_team", "title", "points", "cumulative_points", "cumulative_goal_difference", "rank"]] \
        .sort_values(["matchday", "rank"]) \
        .reset_index(drop=True)

print(compute_standings(games))