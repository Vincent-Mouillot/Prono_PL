import sqlite3
import pandas as pd
import numpy as np
from database import DB_PATH

def compute_avg_goals(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, window: str = "all"):

    df_teams = df_teams.sort_values(["id_team", "date"]).copy()
    df_teams["date"] = pd.to_datetime(df_teams["date"])
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])

    if window == "all":
        # Cumulative sum reset every season (defaults to 1 goal/match on the 1st match)
        group_key = ["id_team", "season"]
        avg_G_for = df_teams.groupby(group_key)["scored"].cumsum() / (df_teams.groupby(group_key)["scored"].cumcount() + 1)
        avg_G_against = df_teams.groupby(group_key)["missed"].cumsum() / (df_teams.groupby(group_key)["missed"].cumcount() + 1)
    else:
        group_key = ["id_team"]
        int_window = int(window)
        avg_G_for = df_teams.groupby("id_team")["scored"].transform(
            lambda x: x.rolling(int_window, min_periods=1).mean()
        )
        avg_G_against = df_teams.groupby("id_team")["missed"].transform(
            lambda x: x.rolling(int_window, min_periods=1).mean()
        )

    # Shift back one match (same group) → previous match's value
    df_teams["avg_G_for"] = avg_G_for.groupby([df_teams[k] for k in group_key]).shift(1)
    df_teams["avg_G_against"] = avg_G_against.groupby([df_teams[k] for k in group_key]).shift(1)

    df_teams = df_teams[["id_team", "title", "h_a", "date", "avg_G_for", "avg_G_against"]]
    teams_h = df_teams.loc[df_teams["h_a"] == "h"].drop("h_a", axis=1)
    teams_a = df_teams.loc[df_teams["h_a"] == "a"].drop("h_a", axis=1)

    df_calendar_feature = df_calendar.merge(
        teams_h,
        left_on=["h_team", "datetime"],
        right_on=["title", "date"],
        how="left"
    ).merge(
        teams_a,
        left_on=["a_team", "datetime"],
        right_on=["title", "date"],
        how="left",
        suffixes=["_h", "_a"]
    )

    return df_calendar_feature[list(df_calendar.columns) + ["avg_G_for_h", "avg_G_against_h", "avg_G_for_a", "avg_G_against_a"]]

def compute_avg_goals_feature(df_calendar: pd.DataFrame):
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    df_calendar = compute_avg_goals(teams, df_calendar).rename(columns={"avg_G_for_h": "avg_G_for_h_saison", 
                                                                        "avg_G_against_h": "avg_G_against_h_saison",
                                                                        "avg_G_for_a": "avg_G_for_a_saison", 
                                                                        "avg_G_against_a": "avg_G_against_a_saison"})
    df_calendar = compute_avg_goals(teams, df_calendar, window="5").rename(columns={"avg_G_for_h": "avg_G_for_h_window", 
                                                                        "avg_G_against_h": "avg_G_against_h_window",
                                                                        "avg_G_for_a": "avg_G_for_a_window", 
                                                                        "avg_G_against_a": "avg_G_against_a_window"})
    df_calendar = compute_avg_goals(teams, df_calendar, window="1").rename(columns={"avg_G_for_h": "avg_G_for_h_match", 
                                                                        "avg_G_against_h": "avg_G_against_h_match",
                                                                        "avg_G_for_a": "avg_G_for_a_match", 
                                                                        "avg_G_against_a": "avg_G_against_a_match"})

    avg_goals_cols = ["avg_G_for_h_saison", 
                      "avg_G_against_h_saison", 
                      "avg_G_for_a_saison", 
                      "avg_G_against_a_saison", 
                      "avg_G_for_h_window", 
                      "avg_G_against_h_window",
                      "avg_G_for_a_window",
                      "avg_G_against_a_window",
                      "avg_G_for_h_match",
                      "avg_G_against_h_match",
                      "avg_G_for_a_match",
                      "avg_G_against_a_match"]
    df_calendar[avg_goals_cols] = df_calendar[avg_goals_cols].fillna(1)

    return df_calendar


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()
    compute_avg_goals_feature(calendar)