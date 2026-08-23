import sqlite3
import pandas as pd
from database.get_cloud_db import DB_PATH


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
        ranking.rename(columns={"title": col, "rank": f"rank_{col}"}),
        on="datetime",
        by=col,
        direction="backward",
        allow_exact_matches=False
    )

    return result


def compute_ranking(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, df_initial_rank: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the ranking of all teams for each date where a game is played.
    And create columns 'diff_rank_h' and 'diff_rank_a' as the ranking difference before a game.
    For the first game of a season use a df with hard coded rank.

    Args:
        df_teams:        teams stats filtered by season
        df_calendar:     games dataframe filtered by season
        df_initial_rank: the initial rank of the season (last rank of the previous season)

    Returns:
        df_calendar with added ranking columns
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

    # For the first game of every team, add the initial rank of the previous season
    df_initial_rank["snapshot_date"] = min(all_dates)
    df_initial_rank["datetime"] = pd.to_datetime(df_initial_rank["snapshot_date"])

    ranking = pd.concat([df_initial_rank, ranking])

    df_calendar_ranked = add_last_ranking(
        add_last_ranking(df_calendar, ranking, "h_team"),
        ranking,
        "a_team"
    )

    df_calendar_ranked["diff_rank_h"] = df_calendar_ranked["rank_a_team"] - df_calendar_ranked["rank_h_team"]
    df_calendar_ranked["diff_rank_a"] = df_calendar_ranked["rank_h_team"] - df_calendar_ranked["rank_a_team"]

    return df_calendar_ranked


# ── Main function ─────────────────────────────────────────────────────────────

def compute_ranking_feature(df_calendar: pd.DataFrame, season: str) -> pd.DataFrame:
    """Compute the ranking feature for a given season and return the enriched calendar."""

    con = sqlite3.connect(DB_PATH)

    # Filter teams_stats by season to avoid mixing seasons
    teams = pd.read_sql_query(
        "SELECT * FROM teams_stats WHERE season = ?;",
        con,
        params=(int(season),)
    )
    initial_rank = pd.read_sql_query(
        "SELECT title, rank FROM initial_ranking WHERE season = ?;",
        con,
        params=(int(season),)
    )

    con.close()

    # Filter calendar by season to avoid mixing seasons
    df_calendar = df_calendar.copy()
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])
    year = int(season)
    df_season = df_calendar[
        ((df_calendar["datetime"].dt.month >= 8) & (df_calendar["datetime"].dt.year == year)) |
        ((df_calendar["datetime"].dt.month < 8) & (df_calendar["datetime"].dt.year == year + 1))
    ].copy()

    return compute_ranking(teams, df_season, initial_rank)


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()
    result = compute_ranking_feature(calendar, season="2025")
    print(result[["datetime", "h_team", "a_team", "rank_h_team", "rank_a_team", "diff_rank_h"]].head(10))
