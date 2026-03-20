import sqlite3
import pandas as pd
import numpy as np
from database import DB_PATH

def compute_ewp(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, window: str = "all"):

    df_teams = df_teams.sort_values(["id_team", "date"]).copy()
    df_teams["date"] = pd.to_datetime(df_teams["date"])
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])

    if window == "all":
        npxG_for = df_teams.groupby("id_team")["npxG"].cumsum()
        npxG_against = df_teams.groupby("id_team")["npxGA"].cumsum()
    else:
        int_window = int(window)
        npxG_for = df_teams.groupby("id_team")["npxG"].transform(
            lambda x: x.rolling(int_window, min_periods=1).sum()
        )
        npxG_against = df_teams.groupby("id_team")["npxGA"].transform(
            lambda x: x.rolling(int_window, min_periods=1).sum()
        )

    # Décalage d'un match en arrière par équipe → valeur du match précédent
    df_teams["npxG_for"] = npxG_for.groupby(df_teams["id_team"]).shift(1)
    df_teams["npxG_against"] = npxG_against.groupby(df_teams["id_team"]).shift(1)

    denom = df_teams["npxG_for"] ** 2 + df_teams["npxG_against"] ** 2
    df_teams["ewp"] = np.where(denom == 0, 0.5, df_teams["npxG_for"] ** 2 / denom)

    df_teams = df_teams[["id_team", "title", "h_a", "date", "npxG_for", "npxG_against", "ewp"]]
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

    return df_calendar_feature[list(df_calendar.columns) + ["ewp_h", "ewp_a"]]


def compute_ewp_feature(df_calendar: pd.DataFrame):
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    df_calendar = compute_ewp(teams, df_calendar).rename(columns={"ewp_h": "ewp_h_saison", "ewp_a": "ewp_a_saison"})
    df_calendar = compute_ewp(teams, df_calendar, window="5").rename(columns={"ewp_h": "ewp_h_window", "ewp_a": "ewp_a_window"})
    df_calendar = compute_ewp(teams, df_calendar, window="1").rename(columns={"ewp_h": "ewp_h_match", "ewp_a": "ewp_a_match"})

    ewp_cols = ["ewp_h_saison", "ewp_a_saison", "ewp_h_window", "ewp_a_window", "ewp_h_match", "ewp_a_match"]
    df_calendar[ewp_cols] = df_calendar[ewp_cols].fillna(0.5)

    return df_calendar


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()
    compute_ewp_feature(calendar)