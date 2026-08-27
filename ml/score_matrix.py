import sqlite3

import numpy as np
import pandas as pd
from scipy.stats import poisson

from database.get_cloud_db import DB_PATH
from ml.dixon_coles_rho_estimator import dixon_coles_tau

# A full PL season is 380 * 2 = 760 team-match rows. Seasons below this are
# still in progress and are excluded from the ratio estimate.
MIN_SEASON_ROWS = 600

# Complete seasons used to estimate goals / npxG. Deliberately short: the
# relationship broke between the 2023 and 2024 seasons (ratio ~1.05 before,
# ~0.96 after, t ~ 4.3). Pooling further back mixes two regimes and lands on a
# value that is wrong for both.
RATIO_SEASONS = 2

# Outside this range the ratio is more likely a data problem — a stale scrape, a
# broken join, an upstream model change — than a real shift, so we surface it
# instead of silently rescaling every prediction.
RATIO_BOUNDS = (0.85, 1.15)


# ── npxG → goals ──────────────────────────────────────────────────────────────

def fit_goals_ratio(n_seasons: int = RATIO_SEASONS, con: sqlite3.Connection | None = None
                    ) -> tuple[float, float]:
    """Estimate E[goals] / E[npxG] for home and away sides on recent complete seasons.

    The model is trained on npxG, so its output is a *non-penalty expected goals*
    rate. score_matrix needs an actual goal rate. The gap has two components that
    partly cancel: penalties add ~+0.10 goals per side per match, while npxG has
    been running above realised goals since the 2024 season. Measuring the total
    end to end captures both without having to model either.

    Home and away are estimated separately: home teams win more penalties, and
    they convert their npxG slightly worse, so a single pooled constant would
    overstate home advantage once translated into goals.

    Returns:
        (ratio_home, ratio_away), each to be multiplied by a predicted npxG.
    """
    owns_con = con is None
    con = con or sqlite3.connect(DB_PATH)
    try:
        agg = pd.read_sql_query(
            "SELECT season, h_a, SUM(scored) AS goals, SUM(npxG) AS npxg, COUNT(*) AS n "
            "FROM teams_stats GROUP BY season, h_a;",
            con,
        )
    finally:
        if owns_con:
            con.close()

    if agg.empty:
        raise ValueError("fit_goals_ratio: teams_stats is empty")

    rows_per_season = agg.groupby("season")["n"].sum()
    complete = rows_per_season[rows_per_season >= MIN_SEASON_ROWS].index
    if len(complete) == 0:
        raise ValueError(
            f"fit_goals_ratio: no season reaches {MIN_SEASON_ROWS} rows "
            f"(largest: {rows_per_season.max()})"
        )

    used = sorted(complete)[-n_seasons:]
    window = agg[agg["season"].isin(used)]

    ratios = []
    for side in ("h", "a"):
        s = window[window["h_a"] == side]
        if s.empty or s["npxg"].sum() == 0:
            raise ValueError(f"fit_goals_ratio: no usable '{side}' rows in seasons {used}")
        ratios.append(float(s["goals"].sum() / s["npxg"].sum()))

    lo, hi = RATIO_BOUNDS
    for side, r in zip(("home", "away"), ratios):
        if not lo <= r <= hi:
            print(
                f"WARNING fit_goals_ratio: {side} ratio {r:.4f} outside {RATIO_BOUNDS} "
                f"on seasons {used} — check the scrape and the npxG join before trusting it"
            )

    return ratios[0], ratios[1]


# ── Score matrix ──────────────────────────────────────────────────────────────

def score_matrix(lam: float, mu: float, rho: float, max_goals: int = 6) -> np.ndarray:
    """Dixon-Coles corrected joint probability matrix P(home=i, away=j) for i, j in [0, max_goals].

    lam and mu are *goal* rates, not npxG — see fit_goals_ratio.
    """
    goals = np.arange(max_goals + 1)
    p_home = poisson.pmf(goals, lam)
    p_away = poisson.pmf(goals, mu)

    x, y = np.meshgrid(goals, goals, indexing="ij")
    matrix = np.outer(p_home, p_away) * dixon_coles_tau(x, y, lam, mu, rho)

    return matrix / matrix.sum()  # renormalize after truncation at max_goals


def score_matrices(
    df: pd.DataFrame,
    rho: float,
    max_goals: int = 6,
    ratio: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """
    Build one Dixon-Coles score matrix per match from a long-format predictions df
    (one row per team side, with 'id', 'is_home', 'xg_predicted').

    'xg_predicted' is an npxG rate; it is converted to a goal rate before the
    matrix is built, otherwise every distribution is shifted and the draw is
    systematically mispriced.

    Args:
        df: output of ml.predictions.predictions — long format, two rows per match id.
        rho: Dixon-Coles correlation parameter (see fit_rho).
        max_goals: matrix truncated to [0, max_goals] goals per side.
        ratio: (home, away) goals/npxG factors. Estimated from the DB when omitted.

    Returns:
        One row per match id, with 'id', 'lam' and 'mu' (home/away *goal* rates),
        'npxg_home'/'npxg_away' (the raw model output, kept for traceability) and
        'score_matrix' (np.ndarray of shape (max_goals+1, max_goals+1)).
    """
    if ratio is None:
        ratio = fit_goals_ratio()
    c_home, c_away = ratio

    home = df.loc[df["is_home"] == 1, ["id", "xg_predicted"]].rename(
        columns={"xg_predicted": "npxg_home"}
    )
    away = df.loc[df["is_home"] == 0, ["id", "xg_predicted"]].rename(
        columns={"xg_predicted": "npxg_away"}
    )

    matches = home.merge(away, on="id")
    matches["lam"] = matches["npxg_home"] * c_home
    matches["mu"] = matches["npxg_away"] * c_away

    matches["score_matrix"] = matches.apply(
        lambda row: score_matrix(row["lam"], row["mu"], rho, max_goals), axis=1
    )

    return matches[["id", "npxg_home", "npxg_away", "lam", "mu", "score_matrix"]]


if __name__ == "__main__":
    c_home, c_away = fit_goals_ratio()
    print(f"goals/npxG ratio — home {c_home:.4f} | away {c_away:.4f}")

    npxg_h, npxg_a, rho = 1.60, 1.20, -0.05
    outcomes = lambda m: (np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum())

    print(f"\nnpxG predicted: {npxg_h} / {npxg_a}, rho {rho}")
    for label, (ch, ca) in (("uncorrected", (1.0, 1.0)), ("corrected", (c_home, c_away))):
        m = score_matrix(npxg_h * ch, npxg_a * ca, rho)
        h, d, a = outcomes(m)
        row, col = np.unravel_index(np.argmax(m), m.shape)
        print(f"  {label:<12} 1X2 {h:.4f}/{d:.4f}/{a:.4f}  P(0-0)={m[0, 0]:.4f}  modal={row}-{col}")