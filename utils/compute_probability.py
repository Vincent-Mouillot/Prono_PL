import numpy as np
import pandas as pd


def compute_proba(df: pd.DataFrame) -> pd.DataFrame:
    """Derive home/draw/away win probabilities from each match's score matrix.

    score_matrix[i, j] = P(home goals=i, away goals=j):
      - home win: home > away -> lower triangle (k=-1)
      - draw: home == away -> diagonal
      - away win: away > home -> upper triangle (k=1)
    """
    df = df.copy()
    df["pct_home"] = df["score_matrix"].apply(lambda m: np.tril(m, k=-1).sum().round(4))
    df["pct_draw"] = df["score_matrix"].apply(lambda m: np.trace(m).round(4))
    df["pct_away"] = df["score_matrix"].apply(lambda m: np.triu(m, k=1).sum().round(4))
    return df

def compute_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pct_score"] = df["score_matrix"].apply(lambda m: m.max().round(4))

    def most_likely_score(m):
        row, col = np.unravel_index(np.argmax(m), m.shape)
        return f"{row} - {col}"

    df["score"] = df["score_matrix"].apply(most_likely_score)
    return df