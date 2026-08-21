# ml/training.py
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import RFECV
from sklearn.metrics import mean_squared_error
from pathlib import Path

from utils import get_season_from_date

MLFLOW_TRACKING_URI = "sqlite:///" + str(Path(__file__).resolve().parent.parent / "mlflow.db")

RF_PARAMS = {"n_estimators": 100, "max_depth": 5, "random_state": 42}


def _prepare_training_data(df: pd.DataFrame):
    """Sort by date, tag each row with its season, and build expanding-window
    train/test index pairs — one per season, skipping the first (not enough history)."""
    df_train = df.loc[~df["xg"].isnull()].sort_values("datetime").reset_index(drop=True)
    df_train["season"] = pd.to_datetime(df_train["datetime"]).apply(get_season_from_date)

    X = df_train.drop(columns=["id", "datetime", "xg", "season"])
    y = df_train["xg"]
    seasons = df_train["season"]

    cv_splits = [
        (seasons[seasons < season].index.to_numpy(), seasons[seasons == season].index.to_numpy())
        for season in sorted(seasons.unique())[1:]
    ]

    return X, y, seasons, cv_splits


def select_features(df: pd.DataFrame, min_features: int = 1) -> list:
    """
    Backward feature selection via RFECV: starts from all features, drops the
    least important one at each round (RandomForestRegressor.feature_importances_),
    refits on the same expanding per-season CV splits as train() (no temporal leakage),
    and keeps the subset with the best mean RMSE.

    Returns the list of selected feature names.
    """
    X, y, _, cv_splits = _prepare_training_data(df)

    selector = RFECV(
        estimator=RandomForestRegressor(**RF_PARAMS),
        step=1,
        min_features_to_select=min_features,
        cv=cv_splits,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
    )
    selector.fit(X, y)

    selected = X.columns[selector.support_].tolist()
    dropped = X.columns[~selector.support_].tolist()
    # cv_results_["n_features"] is ascending (min_features_to_select -> n_total) — look up by value, not by guessed offset
    best_idx = np.where(selector.cv_results_["n_features"] == selector.n_features_)[0][0]
    best_rmse = -selector.cv_results_["mean_test_score"][best_idx]

    print(f"Features sélectionnées ({len(selected)}/{len(X.columns)}), RMSE CV: {best_rmse:.4f}")
    print(f"  gardées : {selected}")
    print(f"  retirées : {dropped}")

    return selected


def train(df: pd.DataFrame):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Prono_PL")

    X, y, seasons, cv_splits = _prepare_training_data(df)

    params = RF_PARAMS
    rmse_scores = []

    with mlflow.start_run(run_name="xg_timeseries_cv"):
        for season, (train_idx, test_idx) in zip(sorted(seasons.unique())[1:], cv_splits):
            X_train, X_test = X.loc[train_idx], X.loc[test_idx]
            y_train, y_test = y.loc[train_idx], y.loc[test_idx]

            model = RandomForestRegressor(**params)
            model.fit(X_train, y_train)

            rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
            rmse_scores.append(rmse)
            mlflow.log_metric("rmse_fold", rmse, step=int(season))
            print(f"Saison {season}/{int(season) + 1} — RMSE: {rmse:.4f}")

        mean_rmse = np.mean(rmse_scores)
        std_rmse = np.std(rmse_scores)

        mlflow.log_params(params)
        mlflow.log_metric("rmse_mean", mean_rmse)
        mlflow.log_metric("rmse_std", std_rmse)

        # Réentraîner le modèle final sur toutes les données
        final_model = RandomForestRegressor(**params)
        final_model.fit(X, y)

        importance_df = pd.DataFrame({
            "feature": X.columns,
            "importance": final_model.feature_importances_
        }).sort_values("importance", ascending=False)

        print(importance_df.to_string())
        mlflow.log_table(importance_df, artifact_file="feature_importances.json")

        mlflow.sklearn.log_model(final_model, name="model_xg")

        print(f"\nRMSE moyen : {mean_rmse:.4f} ± {std_rmse:.4f}")


if __name__ == "__main__":
    df = pd.read_csv("outputs/df_preprocessed.csv")
    train(df)