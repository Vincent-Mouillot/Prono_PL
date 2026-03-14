import sqlite3
import pandas as pd

DB_NAME = "understats_database.db"

con = sqlite3.connect(DB_NAME)

calendar = pd.read_sql_query("SELECT * FROM games;", con)

teams = pd.read_sql_query("SELECT * FROM teams_stats;", con)

initial_rank = pd.read_sql_query("SELECT title, rank FROM initial_ranking WHERE season = (SELECT MAX(season) FROM initial_ranking);", con)

def add_last_ranking(df_calendar: pd.DataFrame, df_ranking: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Merge the last known ranking onto the calendar for a given team column.
    Uses merge_asof to find the latest snapshot strictly before each match datetime.

    Args:
        df_calendar: games dataframe with a 'datetime' column
        df_ranking:  ranking snapshots with 'title', 'datetime', 'rank' columns
        col:         team column to join on, either 'h_team' or 'a_team'

    Returns:
        df_calendar with an added 'rank_{col}' column
    """
    if col not in ["h_team", "a_team"]:
        raise ValueError("Give a valid column name: 'h_team' or 'a_team'")

    calendar = df_calendar.copy()
    calendar["datetime"] = pd.to_datetime(calendar["datetime"])

    ranking = df_ranking[["title", "datetime", "rank"]].copy()
    ranking = ranking.sort_values("datetime")

    calendar = calendar.sort_values("datetime")

    result = pd.merge_asof(
        calendar,
        ranking.rename(columns={"title": col, "datetime": "datetime", "rank": f"rank_{col}"}),
        on="datetime",
        by=col,
        direction="backward",  # last known ranking strictly before match
        allow_exact_matches=False
    )

    return result

def compute_ranking(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, df_initial_rank: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the ranking of all teams for each date where a game is played.
    And create columns 'diff_rank_h' and 'diff_rank_a' as the ranking difference before a game.
    For the first game of a season use a df with hard coded rank.

    Args:
        df_teams:  teams stats with a 'date', 'matchday', 'results, 'scored', 'missed' column
        df_calendar: games dataframe with a 'datetime' column
        df_initial_rank: the initial rank of the season (last rank of the previous season)

    Returns:
        df_calendar with an added 'rank_{col}' column
    """
    played = df_teams.dropna(subset=["result"]).copy()
    played["datetime"] = pd.to_datetime(played["date"])
    played["date"] = played["datetime"].dt.date
    played = played.sort_values(["id_team", "date"])

    played["matchday"] = played.groupby("id_team").cumcount() + 1
    played["points"] = played["result"].map({"w": 3, "d": 1, "l": 0})
    played["goal_difference"] = played["scored"] - played["missed"]

    played["cumulative_points"] = played.groupby("id_team")["points"].cumsum()
    played["cumulative_goal_difference"] = played.groupby("id_team")["goal_difference"].cumsum()

    # For each unique date, take the latest known standings per team
    all_dates = sorted(played["date"].unique())
    snapshots = []

    for d in all_dates:
        # Last known row per team up to date d
        snapshot = (
            played[played["date"] <= d]
            .sort_values("date")
            .groupby("id_team")
            .last()
            .reset_index()
        )
        snapshot["sort_key"] = (
            snapshot["cumulative_points"] * 1000 +
            snapshot["cumulative_goal_difference"]
        )
        snapshot["rank"] = snapshot["sort_key"].rank(ascending=False, method="min").astype(int)
        snapshot["snapshot_date"] = d
        snapshots.append(snapshot[["snapshot_date", "datetime", "id_team", "title", "matchday",
                                   "cumulative_points", "cumulative_goal_difference", "rank"]])
        
    ranking = pd.concat(snapshots, ignore_index=True)

    # First the game of every team we add the initial rank of last season
    # For this we add the first date of the calendar for each initial rank
    df_initial_rank["snapshot_date"] = min(all_dates)
    df_initial_rank["datetime"] = pd.to_datetime(df_initial_rank["snapshot_date"])

    ranking = pd.concat([df_initial_rank, ranking])

    df_calendar_ranked = add_last_ranking(add_last_ranking(calendar, ranking, "h_team"), ranking, "a_team")

    df_calendar_ranked["diff_rank_h"] = df_calendar_ranked["rank_a_team"] - df_calendar_ranked["rank_h_team"]
    df_calendar_ranked["diff_rank_a"] = df_calendar_ranked["rank_h_team"] - df_calendar_ranked["rank_a_team"]

    return df_calendar_ranked

ranking = compute_ranking(teams, calendar, initial_rank)

print(ranking)