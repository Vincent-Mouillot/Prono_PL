import sqlite3
import numpy as np
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from dateutil.relativedelta import relativedelta

from database import DB_PATH

MIN_MATCHES = 100  # rough heuristic: enough matchdays for a well-posed fit
GRAD_TOL = 1e-2

def _unpack(params, n_teams):
    log_alpha     = np.zeros(n_teams)
    log_alpha[1:] = params[:n_teams -1]
    return log_alpha, params[n_teams - 1:2 * n_teams -1], params[-1]

def neg_log_likelihood(params, n_teams, home_idx, away_idx, goals_h, goals_a):
    log_alpha, log_beta, log_gamma = _unpack(params, n_teams)
    lam = np.exp(log_alpha[home_idx] + log_beta[away_idx] + log_gamma)
    mu  = np.exp(log_alpha[away_idx] + log_beta[home_idx])

    return (lam - goals_h * np.log(lam)).sum() + (mu - goals_a * np.log(mu)).sum()

def neg_log_likelihood_grad(params, n_teams, home_idx, away_idx, goals_h, goals_a):
    log_alpha, log_beta, log_gamma = _unpack(params, n_teams)
    lam = np.exp(log_alpha[home_idx] + log_beta[away_idx] + log_gamma)
    mu  = np.exp(log_alpha[away_idx] + log_beta[home_idx])

    res_h = lam - goals_h
    res_a = mu - goals_a

    d_alpha = (np.bincount(home_idx, res_h, minlength=n_teams)
               + np.bincount(away_idx, res_a, minlength=n_teams))
    d_beta  = (np.bincount(away_idx, res_h, minlength=n_teams)
                   + np.bincount(home_idx, res_a, minlength=n_teams))

    return np.concatenate([d_alpha[1:], d_beta, [res_h.sum()]])

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
    goals_h = df_matches["goals_h"].to_numpy(dtype=float)
    goals_a = df_matches["goals_a"].to_numpy(dtype=float)

    n_teams = len(teams)

    # (n_teams - 1) alphas libres + n_teams betas + 1 gamma
    mean_h, mean_a = goals_h.mean(), goals_a.mean()
    x0 = np.concatenate([
        np.zeros(n_teams - 1),
        np.full(n_teams, np.log(mean_a)),
        [np.log(mean_h / mean_a)]
    ])

    args = (n_teams, home_idx, away_idx, goals_h, goals_a)

    result = minimize(
        neg_log_likelihood,
        x0=x0,
        args=args,
        jac=neg_log_likelihood_grad,
        method="BFGS"
    )

    max_residual = np.max(np.abs(result.jac))
    if max_residual > GRAD_TOL:
        raise RuntimeError(
            f"fit_team_power: no convergence ({result.message}) — "
            f"max residual {max_residual:.4f} goals, NLL {result.fun:.2f}"
        )

    log_alpha, log_beta, log_gamma = _unpack(result.x, n_teams)

    m = log_alpha.mean()
    log_alpha = log_alpha - m
    log_beta = log_beta + m
    
    return pd.DataFrame({
        "team": teams,
        "off_power": np.exp(log_alpha),
        "def_power": np.exp(log_beta),
        "gamma": np.exp(log_gamma),
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


def add_npxg(df_calendar: pd.DataFrame) -> pd.DataFrame:
    """Merge each team's non-penalty xG (understat 'npxG') onto the calendar as npxg_h/npxg_a."""
    con = sqlite3.connect(DB_PATH)
    teams = pd.read_sql_query("SELECT title, h_a, date, npxG FROM teams_stats;", con)
    con.close()

    teams["date"] = pd.to_datetime(teams["date"])
    calendar = df_calendar.copy()
    calendar["datetime"] = pd.to_datetime(calendar["datetime"])

    teams_h = teams.loc[teams["h_a"] == "h", ["title", "date", "npxG"]].rename(columns={"npxG": "npxg_h"})
    teams_a = teams.loc[teams["h_a"] == "a", ["title", "date", "npxG"]].rename(columns={"npxG": "npxg_a"})

    calendar = calendar.merge(
        teams_h, left_on=["h_team", "datetime"], right_on=["title", "date"], how="left"
    ).drop(columns=["title", "date"])
    calendar = calendar.merge(
        teams_a, left_on=["a_team", "datetime"], right_on=["title", "date"], how="left"
    ).drop(columns=["title", "date"])

    return calendar


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
        df_calendar with added 'npxg_h', 'npxg_a', 'off_power_h', 'def_power_h',
        'off_power_a', 'def_power_a', 'gamma' columns
    """
    PROMOTED_FILL = {
        "off_power_h": 0.6, "def_power_h": 1.4,
        "off_power_a": 0.6, "def_power_a": 1.4,
    }
    GAMMA_FILL = 1.3

    df_calendar = add_npxg(df_calendar)

    played = df_calendar.dropna(subset=["npxg_h", "npxg_a"]).copy()
    played["goals_h"] = played["npxg_h"]
    played["goals_a"] = played["npxg_a"]
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

    power_cols = ["off_power_h", "def_power_h", "off_power_a", "def_power_a"]

    early = df_calendar_power["gamma"].isna()

    df_calendar_power.loc[early, power_cols] = 1.0
    df_calendar_power["gamma"] = df_calendar_power["gamma"].fillna(GAMMA_FILL)

    # Rest of NaN : promoted teams
    n_promoted = df_calendar_power[power_cols].isna().any(axis=1).sum()
    df_calendar_power = df_calendar_power.fillna(PROMOTED_FILL)

    print(f"team_power : {early.sum()} games before snapshot, {n_promoted} games with promoted team")

    return df_calendar_power


if __name__ == "__main__":
    import sqlite3
    from database.get_cloud_db import DB_PATH

    con = sqlite3.connect(DB_PATH)
    games = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()

    result = compute_team_power_feature(games)
    print(result[["datetime", "h_team", "a_team", "off_power_h", "def_power_h", "off_power_a", "def_power_a", "gamma"]].tail(10))
