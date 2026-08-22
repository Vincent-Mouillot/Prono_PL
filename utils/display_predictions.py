import pandas as pd
import sqlite3
from database.get_cloud_db import DB_PATH


def display_predictions(df_predictions: pd.DataFrame) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df_games = pd.read_sql_query("SELECT id, h_team_short, a_team_short FROM games;", con)
    con.close()

    df_games = df_games.merge(df_predictions, on="id", how="inner")
    df_games = df_games[["id", "h_team_short", "pct_home", "pct_draw", "pct_away", "a_team_short", "score", "pct_score"]]
    df_games.rename(columns={"h_team_short": "Home",
                             "pct_home": "H %",
                             "pct_draw": "D %",
                             "pct_away": "A %",
                             "a_team_short": "Away",
                             "score": "Score",
                             "pct_score": "Score %"}, 
                             inplace=True)

    return df_games