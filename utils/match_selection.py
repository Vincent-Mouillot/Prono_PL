import pandas as pd
from datetime import date, timedelta

def match_selection(df: pd.DataFrame, nb_days: int = 0):
    if nb_days < 0:
        raise ValueError(f"nb_days must be >= 0, got {nb_days}")

    df_coming = df.loc[df["xg"].isnull()].sort_values("datetime").reset_index(drop=True)
    today = pd.Timestamp(date.today())
    return df_coming.loc[pd.to_datetime(df_coming["datetime"]).dt.date <= (today.date() + timedelta(days=nb_days))]