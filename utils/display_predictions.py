import pandas as pd
import sqlite3
from database.get_cloud_db import DB_PATH


def display_predictions(df_predictions: pd.DataFrame) -> str:
    con = sqlite3.connect(DB_PATH)
    df_games = pd.read_sql_query("SELECT id, h_team_short, a_team_short FROM games;", con)
    con.close()

    df_games = df_games.merge(df_predictions, on="id", how="inner")

    lines = [
        f"{row.h_team_short} {row.pct_home * 100:.0f}%-{row.pct_draw * 100:.0f}%-{row.pct_away * 100:.0f}% "
        f"{row.a_team_short} | {row.score} ({row.pct_score * 100:.0f}%)"
        for row in df_games.itertuples()
    ]
    return "\n".join(lines)
