import sqlite3
from datetime import datetime

import pandas as pd

from database.get_cloud_db import DB_PATH

PREDICTION_COLUMNS = ["id", "lam", "mu", "pct_home", "pct_draw", "pct_away", "score", "pct_score"]


def save_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """Upsert predictions into the predictions table, keyed by match id."""
    df = df[PREDICTION_COLUMNS].copy()
    df["predicted_at"] = datetime.now().isoformat(timespec="seconds")

    con = sqlite3.connect(DB_PATH)
    con.executemany(
        f"INSERT OR REPLACE INTO predictions ({', '.join(df.columns)}) "
        f"VALUES ({', '.join(['?'] * len(df.columns))})",
        df.itertuples(index=False, name=None)
    )
    con.commit()
    con.close()

    return df
