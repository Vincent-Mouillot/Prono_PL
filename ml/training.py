# ml/training.py
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.linear_model import PoissonRegressor
from sklearn.feature_selection import RFECV
from sklearn.metrics import mean_poisson_deviance
from pathlib import Path
from datetime import datetime, date

from ml.preprocessing import NON_FEATURE_COLS
from utils import get_season_from_date

MLFLOW_TRACKING_URI = "sqlite:///" + str(Path(__file__).resolve().parent.parent / "mlflow.db")
MLFLOW_EXPERIMENT_NAME = "Prono_PL"

MODEL_PARAMS = {"alpha": 1e-6, "max_iter": 1000}
MIN_TEST_ROWS = 200

def make_model():
    return PoissonRegressor(**MODEL_PARAMS)

def dc_baseline(X: pd.DataFrame, scale: float = 1.0):
    """DC pur, zéro modèle — le plancher que le modèle doit battre."""
    return scale * np.exp(X["log_off_power"] + X["log_def_power_opp"] + X.get("log_gamma_home", 0))

def days_since_last_training():
    """Days since the last MLflow training run, or None if no run exists yet."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
    if experiment is None:
        return None

    runs = client.search_runs(experiment.experiment_id, order_by=["start_time DESC"], max_results=1)
    if not runs:
        return None

    last_run_date = datetime.fromtimestamp(runs[0].info.start_time / 1000).date()
    return (date.today() - last_run_date).days


def _prepare_training_data(df: pd.DataFrame):
    """Sort by date, tag each row with its season, and build expanding-window
    train/test index pairs — one per season, skipping the first (not enough history)."""
    df_train = df.loc[~df["npxg"].isnull()].sort_values("datetime").reset_index(drop=True)
    df_train["season"] = pd.to_datetime(df_train["datetime"]).apply(get_season_from_date)

    X = df_train.drop(columns=NON_FEATURE_COLS + ["season"])
    y = df_train["npxg"]
    seasons = df_train["season"]

    cv_splits = [
        (season,
         seasons[seasons < season].index.to_numpy(),
         seasons[seasons == season].index.to_numpy())
        for season in sorted(seasons.unique())[1:]
    ]
    cv_splits = [s for s in cv_splits if len(s[2]) >= MIN_TEST_ROWS]

    return X, y, seasons, cv_splits

    return X, y, seasons, cv_splits



def train(df: pd.DataFrame):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    X, y, seasons, cv_splits = _prepare_training_data(df)

    params = MODEL_PARAMS
    dev_scores = []

    with mlflow.start_run(run_name="xg_timeseries_cv"):
        for season, train_idx, test_idx in cv_splits:
            X_train, X_test = X.loc[train_idx], X.loc[test_idx]
            y_train, y_test = y.loc[train_idx], y.loc[test_idx]

            model = make_model()
            model.fit(X_train, y_train)

            dev = mean_poisson_deviance(y_test, model.predict(X_test))
            scale = y_train.mean() / dc_baseline(X_train).mean()
            dev_base = mean_poisson_deviance(y_test, dc_baseline(X_test, scale))
            dev_scores.append(dev)

            mlflow.log_metric("poisson_deviance_fold", dev, step=int(season))
            mlflow.log_metric("poisson_deviance_baseline_fold", dev_base, step=int(season))
            print(f"Season {season}/{int(season)+1} — deviance: {dev:.4f} (DC seul: {dev_base:.4f})")

        mean_dev = np.mean(dev_scores)
        std_dev = np.std(dev_scores)

        mlflow.log_params(params)
        mlflow.log_metric("dev_mean", mean_dev)
        mlflow.log_metric("dev_std", std_dev)

        # Retrain the final model on all the data
        final_model = make_model()
        final_model.fit(X, y)

        coef_df = pd.DataFrame({
            "feature": X.columns,
            "coef": final_model.coef_,
        }).reindex(final_model.coef_.argsort()[::-1])
        print(f"intercept: {final_model.intercept_:.4f}")
        print(coef_df.to_string())
        mlflow.log_table(coef_df, artifact_file="coefficients.json")

        mlflow.sklearn.log_model(final_model, name="model_xg")

        print(f"\nDeviance moyen : {mean_dev:.4f} ± {std_dev:.4f}")


if __name__ == "__main__":
    df = pd.read_csv("outputs/df_preprocessed.csv")
    train(df)