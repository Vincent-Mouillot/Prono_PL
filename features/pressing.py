import sqlite3
import pandas as pd
from database import DB_PATH
from datetime import datetime

PPDA_WINDOW = 5


# ── Computation ───────────────────────────────────────────────────────────────

def _asof_join(df_calendar: pd.DataFrame, snapshots: pd.DataFrame, team_col: str) -> pd.DataFrame:
    """Merge each team's latest known PPDA snapshot strictly before the match datetime.

    Same pattern as features.team_power.add_last_power: an exact-date merge only
    finds a row for matches already played, so every future fixture would join to
    nothing and fall back to the league constant. merge_asof looks back to the
    team's last played match instead, which also works for fixtures not yet played.
    """
    suffix = "_h" if team_col == "h_team" else "_a"
    snap = snapshots.rename(columns={"title": team_col, "date": "datetime", "ppda": f"ppda{suffix}"})
    snap = snap[[team_col, "datetime", f"ppda{suffix}"]].sort_values("datetime")

    return pd.merge_asof(
        df_calendar.sort_values("datetime"),
        snap,
        on="datetime",
        by=team_col,
        direction="backward",
        allow_exact_matches=False,
    )


def compute_ppda(df_teams: pd.DataFrame, df_calendar: pd.DataFrame, window: int = PPDA_WINDOW):
    """Rolling PPDA (passes allowed per defensive action) over the last `window` matches.

    Averaging the per-match ratio would let a match with very few defensive
    actions (a tiny, noisy denominator) swing the average as much as a match
    with a normal number of actions. Summing ppda_att and ppda_def separately
    over the window before dividing keeps every match weighted by its actual
    volume of actions.

    Each row's rolling value covers matches up to and including that row's own
    match, tagged with that match's date, and is looked up on the calendar with
    `allow_exact_matches=False` — the calendar row for that same match therefore
    always lands on the *previous* snapshot, i.e. only data strictly before
    kickoff, same as a shift(1) would give, but it also resolves for a fixture
    that hasn't been played yet (see `_asof_join`).

    Lower PPDA = more intense pressing (fewer opponent passes allowed before a
    defensive action).
    """
    df_teams = df_teams.sort_values(["id_team", "date"]).reset_index(drop=True).copy()
    df_teams["date"] = pd.to_datetime(df_teams["date"])

    df_calendar = df_calendar.copy()  # don't mutate the caller's dataframe
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])

    roll_att = df_teams.groupby("id_team")["ppda_att"].transform(
        lambda x: x.rolling(window, min_periods=1).sum()
    )
    roll_def = df_teams.groupby("id_team")["ppda_def"].transform(
        lambda x: x.rolling(window, min_periods=1).sum()
    )
    df_teams["ppda"] = roll_att / roll_def

    snapshots = df_teams[["id_team", "title", "date", "ppda"]]

    df_calendar_feature = _asof_join(_asof_join(df_calendar, snapshots, "h_team"), snapshots, "a_team")

    return df_calendar_feature[list(df_calendar.columns) + ["ppda_h", "ppda_a"]]


# ── Entry point ───────────────────────────────────────────────────────────────

def compute_ppda_feature(df_calendar: pd.DataFrame, window: int = PPDA_WINDOW):
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    df_calendar = compute_ppda(teams, df_calendar, window=window)

    # A team's first matches (window not yet full) fall back to the league-wide
    # ratio rather than 0.5-style arbitrary constant — PPDA has no natural midpoint.
    league_ppda = float(teams["ppda_att"].sum() / teams["ppda_def"].sum())
    ppda_cols = ["ppda_h", "ppda_a"]
    df_calendar[ppda_cols] = df_calendar[ppda_cols].fillna(league_ppda)

    return df_calendar


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    league_ppda = teams["ppda_att"].sum() / teams["ppda_def"].sum()
    print(f"league-wide PPDA (fallback): {league_ppda:.3f}")

    out = compute_ppda_feature(calendar)
    print(f"\nremaining NaNs: {out[['ppda_h', 'ppda_a']].isna().sum().sum()}")
    print("\nMost recent matches:")
    print(out.loc[out["datetime"] >= datetime.today(), ["datetime", "h_team", "a_team", "ppda_h", "ppda_a"]].head(10))

