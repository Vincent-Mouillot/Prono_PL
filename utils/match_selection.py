import pandas as pd
from datetime import date

def match_selection(df: pd.DataFrame):
    df_coming = df.loc[df["xg"].isnull()].sort_values("datetime").reset_index(drop=True)
    today = pd.Timestamp(date.today())
    return df_coming.loc[pd.to_datetime(df_coming["datetime"]).dt.date == today.date()]