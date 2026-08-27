import sqlite3
import pandas as pd
from database import DB_PATH
from datetime import datetime

DEEP_WINDOW = 5


# ── Computation ───────────────────────────────────────────────────────────────

def _asof_join(df_calendar: pd.DataFrame, snapshots: pd.DataFrame, team_col: str, value_col: str) -> pd.DataFrame:
    """Merge each team's latest known snapshot strictly before the match datetime.

    Same pattern as features.pressing._asof_join: merge_asof looks back to the
    team's last played match, which also resolves for a fixture not yet played.
    """
    suffix = "_h" if team_col == "h_team" else "_a"
    snap = snapshots.rename(columns={"title": team_col, "date": "datetime", value_col: f"{value_col}{suffix}"})
    snap = snap[[team_col, "datetime", f"{value_col}{suffix}"]].sort_values("datetime")

    return pd.merge_asof(
        df_calendar.sort_values("datetime"),
        snap,
        on="datetime",
        by=team_col,
        direction="backward",
        allow_exact_matches=False,
    )


def compute_chance_creation(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, window: int = DEEP_WINDOW):
    """Rolling mean of deep completions made (offensive chance creation) and
    conceded (defensive solidity) over the last `window` matches.

    A mean rather than a sum: unlike ewp/ppda, deep and deep_allowed aren't
    reduced to a ratio of each other where the match count would cancel out, so
    nothing corrects the sample-size bias that rolling(window, min_periods=1)
    introduces on a team's first few matches — a sum over 2 games is
    mechanically smaller than a sum over 5, with no relation to the team's
    actual level. A mean stays comparable from matchday 1.

    Each row's rolling mean covers matches up to and including that row's own
    match, tagged with that match's date, and is looked up on the calendar with
    `allow_exact_matches=False` — same point-in-time pattern as
    features.pressing.compute_ppda, so it also resolves for a fixture not yet
    played.
    """
    df_teams = df_teams.sort_values(["id_team", "date"]).reset_index(drop=True).copy()
    df_teams["date"] = pd.to_datetime(df_teams["date"])

    df_calendar = df_calendar.copy()  # don't mutate the caller's dataframe
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])

    df_teams["deep"] = df_teams.groupby("id_team")["deep"].transform(
        lambda x: x.rolling(window, min_periods=1).mean()
    )
    df_teams["deep_allowed"] = df_teams.groupby("id_team")["deep_allowed"].transform(
        lambda x: x.rolling(window, min_periods=1).mean()
    )

    snapshots = df_teams[["id_team", "title", "date", "deep", "deep_allowed"]]

    df_calendar_feature = df_calendar
    for value_col in ["deep", "deep_allowed"]:
        snap = snapshots[["id_team", "title", "date", value_col]]
        df_calendar_feature = _asof_join(
            _asof_join(df_calendar_feature, snap, "h_team", value_col), snap, "a_team", value_col
        )

    return df_calendar_feature[list(df_calendar.columns) + [
        "deep_h", "deep_a", "deep_allowed_h", "deep_allowed_a"
    ]]


# ── Entry point ───────────────────────────────────────────────────────────────

def compute_chance_creation_feature(df_calendar: pd.DataFrame, window: int = DEEP_WINDOW):
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    df_calendar = compute_chance_creation(teams, df_calendar, window=window)

    # min_periods=1 means only a team with zero prior matches on record is ever
    # NaN — fall back to the league-wide mean, same convention as
    # compute_ppda_feature's league_ppda.
    fill = {
        "deep_h": teams["deep"].mean(), "deep_a": teams["deep"].mean(),
        "deep_allowed_h": teams["deep_allowed"].mean(), "deep_allowed_a": teams["deep_allowed"].mean(),
    }
    df_calendar = df_calendar.fillna(fill)

    return df_calendar


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    print(f"league-wide deep (fallback): {teams['deep'].mean():.3f}")
    print(f"league-wide deep_allowed (fallback): {teams['deep_allowed'].mean():.3f}")

    out = compute_chance_creation_feature(calendar)
    cols = ["deep_h", "deep_a", "deep_allowed_h", "deep_allowed_a"]
    print(f"\nremaining NaNs: {out[cols].isna().sum().sum()}")
    print("\nMost recent matches:")
    print(out.loc[out["datetime"] >= datetime.today(), ["datetime", "h_team", "a_team"] + cols].head(10))
