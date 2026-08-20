import sqlite3
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import poisson

from database.get_cloud_db import DB_PATH


def dixon_coles_tau(x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Low-score correction factor applied to the independent Poisson product."""
    tau = np.ones_like(x, dtype=float)
    tau = np.where((x == 0) & (y == 0), 1 - lam * mu * rho, tau)
    tau = np.where((x == 0) & (y == 1), 1 + lam * rho, tau)
    tau = np.where((x == 1) & (y == 0), 1 + mu * rho, tau)
    tau = np.where((x == 1) & (y == 1), 1 - rho, tau)
    return tau


def _neg_log_likelihood(rho: float, goals_h: np.ndarray, goals_a: np.ndarray, lam: np.ndarray, mu: np.ndarray) -> float:
    tau = dixon_coles_tau(goals_h, goals_a, lam, mu, rho)
    if np.any(tau <= 0):
        return 1e10  # rho infeasible for this dataset

    log_lik = np.log(tau) + poisson.logpmf(goals_h, lam) + poisson.logpmf(goals_a, mu)
    return -log_lik.sum()


def fit_rho(df: pd.DataFrame) -> float:
    """
    Estimate the Dixon-Coles rho parameter by maximum likelihood on played matches.

    Args:
        df: matches with columns 'goals_h', 'goals_a', 'xg_h', 'xg_a'.
            xg_h/xg_a are used as the lambda/mu (expected goals) for each historical match.

    Returns:
        The fitted rho.
    """
    played = df.dropna(subset=["goals_h", "goals_a", "xg_h", "xg_a"])

    result = minimize_scalar(
        _neg_log_likelihood,
        bounds=(-1, 1),
        method="bounded",
        args=(
            played["goals_h"].to_numpy(),
            played["goals_a"].to_numpy(),
            played["xg_h"].to_numpy(),
            played["xg_a"].to_numpy(),
        ),
    )
    return result.x


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    games = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()

    rho = fit_rho(games)
    print(f"Fitted rho: {rho:.4f}")
