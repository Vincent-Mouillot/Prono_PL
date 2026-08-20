# ml/training.py
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
from pathlib import Path

from utils import get_season_from_date

MLFLOW_TRACKING_URI = "sqlite:///" + str(Path(__file__).resolve().parent.parent / "mlflow.db")


def train(df: pd.DataFrame):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Prono_PL")

    df_train = df.loc[~df["xg"].isnull()].sort_values("datetime").reset_index(drop=True)
    df_train["season"] = pd.to_datetime(df_train["datetime"]).apply(get_season_from_date)

    X = df_train.drop(columns=["id", "datetime", "xg", "season"])
    y = df_train["xg"]
    seasons = df_train["season"]

    params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    rmse_scores = []

    with mlflow.start_run(run_name="xg_timeseries_cv"):
        for season in sorted(seasons.unique())[1:]:  # skip la première saison, pas assez d'historique
            train_idx = seasons[seasons < season].index
            test_idx  = seasons[seasons == season].index

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