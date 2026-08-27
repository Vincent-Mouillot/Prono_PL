import sqlite3
import pandas as pd
import numpy as np
from database import DB_PATH

# Number of "virtual matches" at the previous season's rate injected into the
# current season's cumulative sum. The prior's weight is K / (K + k), where k is
# the number of matches actually played: 100% on matchday 1, 45% by matchday 7,
# 14% by matchday 38.
# PRIOR_MATCHES = 0 reproduces the old behaviour (0.5 on matchday 1).
PRIOR_MATCHES = 6


# ── Priors ────────────────────────────────────────────────────────────────────

def _season_rates(df_teams: pd.DataFrame) -> pd.DataFrame:
    """Per-team, per-season mean npxG / npxGA, shifted forward by one season.

    The `season + 1` is what forces the match on the *exact* preceding season: a
    team promoted after several years in the Championship finds no prior and falls
    through to the promoted case, instead of inheriting a three-year-old ewp.
    """
    rates = (
        df_teams.groupby(["id_team", "season"])
        .agg(prior_npxG=("npxG", "mean"), prior_npxGA=("npxGA", "mean"))
        .reset_index()
    )
    rates["season"] = rates["season"] + 1
    return rates


def _promoted_rates(df_teams: pd.DataFrame) -> tuple[float, float]:
    """Mean npxG / npxGA of a team during its first season present in the DB.

    The earliest season is excluded: every team is "new" there, so including it
    would measure the league average rather than the promoted teams' profile.
    """
    first_db = df_teams["season"].min()
    first_season = df_teams.groupby("id_team")["season"].transform("min")
    is_new = (first_season == df_teams["season"]) & (df_teams["season"] > first_db)

    if not is_new.any():
        return float(df_teams["npxG"].mean()), float(df_teams["npxGA"].mean())
    return float(df_teams.loc[is_new, "npxG"].mean()), float(df_teams.loc[is_new, "npxGA"].mean())


def _ewp(npxG_for, npxG_against, fallback: float = 0.5):
    denom = npxG_for ** 2 + npxG_against ** 2
    return np.where(denom == 0, fallback, npxG_for ** 2 / denom)


def promoted_ewp(df_teams: pd.DataFrame) -> float:
    """ewp matching the average promoted team's profile — replaces the arbitrary 0.5."""
    pm_for, pm_against = _promoted_rates(df_teams)
    return float(_ewp(pm_for, pm_against))


# ── Computation ───────────────────────────────────────────────────────────────

def compute_ewp(
    df_teams: pd.DataFrame,
    df_calendar: pd.DataFrame,
    window: str = "all",
    prior_matches: int = PRIOR_MATCHES,
):
    df_teams = df_teams.sort_values(["id_team", "date"]).reset_index(drop=True).copy()
    df_teams["date"] = pd.to_datetime(df_teams["date"])

    df_calendar = df_calendar.copy()  # don't mutate the caller's dataframe
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])

    if window == "all":
        group_key = ["id_team", "season"]

        # Prior: K virtual matches at the same team's previous-season rate.
        # merge reindexes, so everything downstream stays aligned on one index.
        df_teams = df_teams.merge(_season_rates(df_teams), on=group_key, how="left")

        pm_for, pm_against = _promoted_rates(df_teams)
        lg_for, lg_against = df_teams["npxG"].mean(), df_teams["npxGA"].mean()

        # Earliest season: nobody has an N-1, so fall back to the league average
        # rather than the promoted profile, which would be wrong for everyone.
        is_first = df_teams["season"] == df_teams["season"].min()
        df_teams["prior_npxG"] = df_teams["prior_npxG"].fillna(
            pd.Series(np.where(is_first, lg_for, pm_for), index=df_teams.index)
        )
        df_teams["prior_npxGA"] = df_teams["prior_npxGA"].fillna(
            pd.Series(np.where(is_first, lg_against, pm_against), index=df_teams.index)
        )

        cum_for = df_teams.groupby(group_key)["npxG"].cumsum()
        cum_against = df_teams.groupby(group_key)["npxGA"].cumsum()

        # Cumulative sum strictly before the current match → 0 on matchday 1 (not
        # NaN), so only the prior survives: matchday-1 ewp == end-of-season N-1 ewp.
        npxG_for = (
            cum_for.groupby([df_teams[k] for k in group_key]).shift(1).fillna(0.0)
            + prior_matches * df_teams["prior_npxG"]
        )
        npxG_against = (
            cum_against.groupby([df_teams[k] for k in group_key]).shift(1).fillna(0.0)
            + prior_matches * df_teams["prior_npxGA"]
        )
    else:
        # Rolling window: grouped on id_team alone, it already spans the off-season
        # and needs no prior. Only a team's very first match is NaN.
        group_key = ["id_team"]
        int_window = int(window)

        roll_for = df_teams.groupby("id_team")["npxG"].transform(
            lambda x: x.rolling(int_window, min_periods=1).sum()
        )
        roll_against = df_teams.groupby("id_team")["npxGA"].transform(
            lambda x: x.rolling(int_window, min_periods=1).sum()
        )
        npxG_for = roll_for.groupby([df_teams[k] for k in group_key]).shift(1)
        npxG_against = roll_against.groupby([df_teams[k] for k in group_key]).shift(1)

    df_teams["npxG_for"] = npxG_for
    df_teams["npxG_against"] = npxG_against
    df_teams["ewp"] = _ewp(df_teams["npxG_for"], df_teams["npxG_against"])

    df_teams = df_teams[["id_team", "title", "h_a", "date", "npxG_for", "npxG_against", "ewp"]]
    teams_h = df_teams.loc[df_teams["h_a"] == "h"].drop("h_a", axis=1)
    teams_a = df_teams.loc[df_teams["h_a"] == "a"].drop("h_a", axis=1)

    df_calendar_feature = df_calendar.merge(
        teams_h,
        left_on=["h_team", "datetime"],
        right_on=["title", "date"],
        how="left",
    ).merge(
        teams_a,
        left_on=["a_team", "datetime"],
        right_on=["title", "date"],
        how="left",
        suffixes=["_h", "_a"],
    )

    return df_calendar_feature[list(df_calendar.columns) + ["ewp_h", "ewp_a"]]


# ── Entry point ───────────────────────────────────────────────────────────────

def compute_ewp_feature(df_calendar: pd.DataFrame, prior_matches: int = PRIOR_MATCHES):
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    df_calendar = compute_ewp(teams, df_calendar, prior_matches=prior_matches).rename(
        columns={"ewp_h": "ewp_h_saison", "ewp_a": "ewp_a_saison"}
    )
    df_calendar = compute_ewp(teams, df_calendar, window="5").rename(
        columns={"ewp_h": "ewp_h_window", "ewp_a": "ewp_a_window"}
    )

    # ewp_saison can no longer be NaN (the prior is always > 0).
    # What remains is a team's very first match, for ewp_window.
    ewp_cols = ["ewp_h_saison", "ewp_a_saison", "ewp_h_window", "ewp_a_window"]
    df_calendar[ewp_cols] = df_calendar[ewp_cols].fillna(promoted_ewp(teams))

    return df_calendar


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    calendar = pd.read_sql_query("SELECT * FROM games;", con)
    teams = pd.read_sql_query("SELECT * FROM teams_stats ORDER BY id_team, date;", con)
    con.close()

    pm_for, pm_against = _promoted_rates(teams)
    print(f"promoted prior: npxG {pm_for:.3f} / npxGA {pm_against:.3f} -> ewp {promoted_ewp(teams):.3f}")

    # Season-to-season persistence of end-of-season ewp: this dictates K.
    # ~0.7-0.8 -> generous K (8-10). < 0.4 -> small K (2-3).
    e = (
        teams.groupby(["id_team", "season"])
        .apply(
            lambda x: x["npxG"].sum() ** 2 / (x["npxG"].sum() ** 2 + x["npxGA"].sum() ** 2),
            include_groups=False,
        )
        .rename("ewp_end")
        .reset_index()
    )
    prev = e.copy()
    prev["season"] = prev["season"] + 1
    joined = e.merge(prev, on=["id_team", "season"], suffixes=("", "_prev")).dropna()
    print(f"ewp correlation, season N vs N-1: {joined['ewp_end'].corr(joined['ewp_end_prev']):.3f} "
          f"(n={len(joined)})")

    out = compute_ewp_feature(calendar)
    print(f"\nremaining NaNs: {out[['ewp_h_saison', 'ewp_a_saison']].isna().sum().sum()}")
    print("\nStart of the 2026 season:")
    print(out.loc[pd.to_datetime(out['datetime']) >= '2026-08-01',
                  ["datetime", "h_team", "a_team", "ewp_h_saison", "ewp_a_saison"]].head(10))