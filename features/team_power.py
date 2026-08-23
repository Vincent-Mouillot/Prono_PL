import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from dateutil.relativedelta import relativedelta

MIN_MATCHES = 100  # rough heuristic: enough matchdays for a well-posed fit


def neg_log_likelihood(params, teams, home_idx, away_idx, goals_h, goals_a):
    n = len(teams)

    log_alpha = np.zeros(n)
    log_alpha[1:] = params[:n-1]        # team 0 = reference, alpha fixed to 1 (log=0)

    log_beta  = params[n-1:2*n-1]
    log_gamma = params[-1]

    lam = np.exp(log_alpha[home_idx] + log_beta[away_idx] + log_gamma)
    mu  = np.exp(log_alpha[away_idx] + log_beta[home_idx])

    return -(poisson.logpmf(goals_h, lam).sum() + poisson.logpmf(goals_a, mu).sum())


def fit_team_power(df_matches: pd.DataFrame) -> pd.DataFrame:
    """
    Fit Dixon-Coles attack (alpha), defense (beta) and home advantage (gamma)
    by maximum likelihood on a fixed set of played matches.

    Args:
        df_matches: played matches with 'h_team', 'a_team', 'goals_h', 'goals_a'.
            Date filtering must be done by the caller — this fits on whatever it's given.

    Returns:
        One row per team, with columns 'team', 'off_power', 'def_power', 'gamma'
        ('gamma' is a single league-wide value, repeated on every row for easy merging).
    """
    codes, teams = pd.factorize(pd.concat([df_matches["h_team"], df_matches["a_team"]]))
    n_matches = len(df_matches)
    home_idx = codes[:n_matches]
    away_idx = codes[n_matches:]
    goals_h = df_matches["goals_h"].to_numpy()
    goals_a = df_matches["goals_a"].to_numpy()

    n_teams = len(teams)
    gamma_init = df_matches["goals_h"].sum() / df_matches["goals_a"].sum()

    # (n_teams - 1) alphas libres + n_teams betas + 1 gamma
    x0 = np.array([1.0] * (n_teams - 1) + [1.0] * n_teams + [gamma_init])

    result = minimize(
        neg_log_likelihood,
        x0=x0,
        args=(teams, home_idx, away_idx, goals_h, goals_a),
        options={"gtol": 1e-4},
    )

    alpha = np.concatenate([[1.0], np.exp(result.x[:n_teams - 1])])
    beta  = np.exp(result.x[n_teams - 1:2 * n_teams - 1])
    gamma = np.exp(result.x[-1])

    return pd.DataFrame({
        "team": teams,
        "off_power": alpha,
        "def_power": beta,
        "gamma": gamma,
    })


def add_last_power(df_calendar: pd.DataFrame, df_power: pd.DataFrame, col: str) -> pd.DataFrame:
    """Merge the last known off_power/def_power snapshot onto the calendar for a given team column."""
    if col not in ["h_team", "a_team"]:
        raise ValueError("Give a valid column name: 'h_team' or 'a_team'")

    calendar = df_calendar.copy()
    calendar["datetime"] = pd.to_datetime(calendar["datetime"])

    suffix = "_h" if col == "h_team" else "_a"
    power = df_power[["team", "datetime", "off_power", "def_power"]].rename(
        columns={"team": col, "off_power": f"off_power{suffix}", "def_power": f"def_power{suffix}"}
    ).sort_values("datetime")

    calendar = calendar.sort_values("datetime")

    return pd.merge_asof(
        calendar,
        power,
        on="datetime",
        by=col,
        direction="backward",
        allow_exact_matches=False,
    )


def add_last_gamma(df_calendar: pd.DataFrame, df_power: pd.DataFrame) -> pd.DataFrame:
    """Merge the last known league-wide gamma snapshot onto the calendar."""
    calendar = df_calendar.copy()
    calendar["datetime"] = pd.to_datetime(calendar["datetime"])

    gamma_snapshots = df_power[["datetime", "gamma"]].drop_duplicates().sort_values("datetime")
    calendar = calendar.sort_values("datetime")

    return pd.merge_asof(
        calendar,
        gamma_snapshots,
        on="datetime",
        direction="backward",
        allow_exact_matches=False,
    )


def compute_team_power_feature(df_calendar: pd.DataFrame, nb_months: int = 12) -> pd.DataFrame:
    """
    Compute Dixon-Coles off_power/def_power/gamma for each date where a game is played,
    using only matches from the trailing `nb_months` window strictly before that date
    (no lookahead — same point-in-time snapshot pattern as compute_ranking).

    Snapshots are recomputed once per calendar month (not per unique match date) —
    refitting ~40 parameters is much heavier than compute_ranking's cumsum, so a
    monthly cadence is used to keep the runtime reasonable.

    Args:
        df_calendar: games dataframe with 'datetime', 'h_team', 'a_team', 'goals_h', 'goals_a'
        nb_months: size of the trailing fitting window, in months

    Returns:
        df_calendar with added 'off_power_h', 'def_power_h', 'off_power_a', 'def_power_a', 'gamma' columns
    """
    played = df_calendar.dropna(subset=["goals_h", "goals_a"]).copy()
    played["datetime"] = pd.to_datetime(played["datetime"])
    played = played.sort_values("datetime")

    all_months = pd.period_range(
        start=played["datetime"].min().to_period("M"),
        end=played["datetime"].max().to_period("M"),
        freq="M",
    )
    snapshots = []

    for period in all_months:
        window_end = period.start_time
        window_start = window_end - relativedelta(months=nb_months)
        window = played[(played["datetime"] < window_end) & (played["datetime"] >= window_start)]

        if len(window) < MIN_MATCHES:
            continue

        power = fit_team_power(window)
        power["datetime"] = window_end
        snapshots.append(power)

    if not snapshots:
        raise ValueError(f"Not enough matches (< {MIN_MATCHES}) in any {nb_months}-month window to fit team power")

    df_power = pd.concat(snapshots, ignore_index=True)
    df_power["datetime"] = pd.to_datetime(df_power["datetime"])  # match calendar's dtype resolution for merge_asof

    df_calendar_power = add_last_power(
        add_last_power(df_calendar, df_power, "h_team"),
        df_power,
        "a_team",
    )
    df_calendar_power = add_last_gamma(df_calendar_power, df_power)

    power_cols = ["off_power_h", "def_power_h", "off_power_a", "def_power_a", "gamma"]
    df_calendar_power[power_cols] = df_calendar_power[power_cols].fillna(1)

    return df_calendar_power


if __name__ == "__main__":
    import sqlite3
    from database.get_cloud_db import DB_PATH

    con = sqlite3.connect(DB_PATH)
    games = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()

    result = compute_team_power_feature(games)
    print(result[["datetime", "h_team", "a_team", "off_power_h", "def_power_h", "off_power_a", "def_power_a", "gamma"]].tail(10))
