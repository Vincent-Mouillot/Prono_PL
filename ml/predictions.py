import pandas as pd
import mlflow
import mlflow.sklearn
from pathlib import Path

MLFLOW_TRACKING_URI = "sqlite:///" + str(Path(__file__).resolve().parent.parent / "mlflow.db")

def load_model():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("Prono_PL")
    runs = client.search_runs(experiment.experiment_id, order_by=["start_time DESC"], max_results=1)
    run_id = runs[0].info.run_id
    return mlflow.sklearn.load_model(f"runs:/{run_id}/model_xg")


def predictions(df: pd.DataFrame) -> pd.DataFrame:
    today_matches = df.copy()

    model = load_model()
    X = today_matches.drop(columns=["id", "datetime", "xg"])
    today_matches = today_matches.copy()
    today_matches["xg_predicted"] = model.predict(X)
    return today_matches