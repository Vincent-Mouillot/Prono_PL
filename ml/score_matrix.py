import numpy as np
import pandas as pd
from scipy.stats import poisson

from ml.dixon_coles_rho_estimator import dixon_coles_tau

def score_matrix(lam: float, mu: float, rho: float, max_goals: int = 6) -> np.ndarray:
    """Dixon-Coles corrected joint probability matrix P(home=i, away=j) for i, j in [0, max_goals]."""
    goals = np.arange(max_goals + 1)
    p_home = poisson.pmf(goals, lam)
    p_away = poisson.pmf(goals, mu)

    x, y = np.meshgrid(goals, goals, indexing="ij")
    matrix = np.outer(p_home, p_away) * dixon_coles_tau(x, y, lam, mu, rho)

    return matrix / matrix.sum()  # renormalize after truncation at max_goals


def score_matrices(df: pd.DataFrame, rho: float, max_goals: int = 6) -> pd.DataFrame:
    """
    Build one Dixon-Coles score matrix per match from a long-format predictions df
    (one row per team side, with 'id', 'is_home', 'xg_predicted').

    Args:
        df: output of ml.predictions.predictions — long format, two rows per match id.
        rho: Dixon-Coles correlation parameter (see fit_rho).
        max_goals: matrix truncated to [0, max_goals] goals per side.

    Returns:
        One row per match id, with columns 'id', 'lam' (home xg),
        'mu' (away xg) and 'score_matrix' (np.ndarray of shape (max_goals+1, max_goals+1)).
    """
    home = df.loc[df["is_home"] == 1, ["id", "xg_predicted"]].rename(columns={"xg_predicted": "lam"})
    away = df.loc[df["is_home"] == 0, ["id", "xg_predicted"]].rename(columns={"xg_predicted": "mu"})

    matches = home.merge(away, on="id")
    matches["score_matrix"] = matches.apply(
        lambda row: score_matrix(row["lam"], row["mu"], rho, max_goals), axis=1
    )

    return matches


if __name__ == "__main__":

    score = score_matrix(1.5, 1.1, -0.07, 4)
    print(score)