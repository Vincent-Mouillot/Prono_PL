from prefect import flow, task
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional

# Database
from database import DB_PATH, init_db, check_db_exists, download_db, upload_db, save_predictions

# Scrapers
from scrapers import get_calendar, get_players_stats, get_teams_stats

# Features
from features import compute_ewp_feature, compute_ranking_feature, compute_team_power_feature

# ML
from ml import preprocessing_function, train, predictions, fit_rho, score_matrices, days_since_last_training

# Utils
from utils import get_current_season, get_season_from_date, match_selection, compute_proba, compute_score, display_predictions

TRAINING_INTERVAL_DAYS = 30

# ── Database tasks ────────────────────────────────────────────────────────────

@task(name="Check DB exists on Google Drive")
def task_check_db_exists() -> bool:
    return check_db_exists()

@task(name="Download DB from Google Drive")
def task_download_db():
    download_db()

@task(name="Init DB")
def task_init_db():
    init_db()

@task(name="Upload DB to Google Drive")
def task_upload_db():
    upload_db()

# ── Utils ─────────────────────────────────────────────────────────────────────

@task(name="Display predictions")
def task_display_predictions(df: pd.DataFrame):
    return display_predictions(df)

@task(name="Save predictions to DB", retries=2, retry_delay_seconds=30)
def task_save_predictions(df: pd.DataFrame) -> pd.DataFrame:
    return save_predictions(df)

# ── Scraping tasks ────────────────────────────────────────────────────────────

@task(name="Scrape calendar", retries=2, retry_delay_seconds=30)
def task_get_calendar(season: str):
    get_calendar(season)

@task(name="Scrape teams stats", retries=2, retry_delay_seconds=30)
def task_get_teams_stats(season: str):
    get_teams_stats(season)

@task(name="Scrape players stats", retries=2, retry_delay_seconds=30)
def task_get_players_stats(season: str):
    get_players_stats(season)


# ── Load tasks ────────────────────────────────────────────────────────────────

@task(name="Load games from DB")
def task_load_games() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()
    return df

@task(name="Load features from DB")
def task_load_features() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM features;", con)
    con.close()
    return df

@task(name="Load available seasons from DB")
def task_load_seasons() -> list:
    con = sqlite3.connect(DB_PATH)
    seasons = pd.read_sql_query(
        "SELECT DISTINCT season FROM teams_stats ORDER BY season;", con
    )["season"].tolist()
    con.close()
    return seasons


# ── Features tasks ────────────────────────────────────────────────────────────

@task(name="Compute ranking difference", retries=2, retry_delay_seconds=30)
def task_compute_ranking(df_calendar: pd.DataFrame, season: str) -> pd.DataFrame:
    return compute_ranking_feature(df_calendar, season)

@task(name="Compute EWP", retries=2, retry_delay_seconds=30)
def task_compute_ewp(df: pd.DataFrame) -> pd.DataFrame:
    return compute_ewp_feature(df)

@task(name="Compute offensive and defensive team power", retries=2, retry_delay_seconds=30)
def task_compute_team_power(df: pd.DataFrame) -> pd.DataFrame:
    return compute_team_power_feature(df)

# ── ML tasks ──────────────────────────────────────────────────────────────────

@task(name="Preprocess data into long format", retries=2, retry_delay_seconds=30)
def task_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    return preprocessing_function(df)

@task(name="Select today matches", retries=2, retry_delay_seconds=30)
def task_match_selection(df: pd.DataFrame, nb_days: int = 0) -> pd.DataFrame:
    return match_selection(df, nb_days)

@task(name="Predict today matches", retries=2, retry_delay_seconds=30)
def task_predictions(df: pd.DataFrame) -> pd.DataFrame:
    return predictions(df)

@task(name="Predict rho estimator for Dixon Coles model", retries=2, retry_delay_seconds=30)
def task_rho_estimator(df: pd.DataFrame) -> pd.DataFrame:
    return fit_rho(df)

@task(name="Build score matrices", retries=2, retry_delay_seconds=30)
def task_score_matrices(df: pd.DataFrame, rho: float, max_goals: int = 6) -> pd.DataFrame:
    return score_matrices(df, rho)

@task(name="Check days since last training")
def task_days_since_last_training() -> Optional[int]:
    return days_since_last_training()

@task(name="Compute probabilties from score matrices", retries=2, retry_delay_seconds=30)
def task_compute_proba(df: pd.DataFrame) -> pd.DataFrame:
    return compute_proba(df) 

@task(name="Compute most probable score", retries=2, retry_delay_seconds=30)
def task_compute_score(df: pd.DataFrame) -> pd.DataFrame:
    return compute_score(df)

# ── Subflows ──────────────────────────────────────────────────────────────────

@flow(name="Database setup flow")
def database_setup_flow():
    """Download DB if it exists on Drive, otherwise init a fresh one."""
    db_exists = task_check_db_exists()
    if db_exists:
        task_download_db()
    else:
        task_init_db()

@flow(name="Scraping flow")
def scraping_flow(season: str):
    """Scrape all data sources for a given season."""
    task_get_calendar(season)
    task_get_players_stats(season)
    task_get_teams_stats(season)

@flow(name="Database upload flow")
def database_upload_flow():
    """Upload the updated DB back to Google Drive."""
    task_upload_db()

@flow(name="Compute features")
def features_flow(force_compute: bool = False):
    """Compute features and write to the features table.

    force_compute=True recomputes the ranking for every season from scratch.
    force_compute=False (default) only recomputes the ranking for the current
    season — past seasons' ranking never changes once played — and reuses
    what's already stored in DB for the rest.
    """
    df_games = task_load_games()
    seasons = task_load_seasons()

    if force_compute:
        # Compute ranking per season then concatenate
        df_all = pd.concat([
            task_compute_ranking(df_games, str(season)) for season in seasons
        ], ignore_index=True)
    else:
        current_season = get_current_season()
        df_current = task_compute_ranking(df_games, current_season)

        existing = task_load_features()
        if existing.empty:
            df_all = df_current
        else:
            existing_season = pd.to_datetime(existing["datetime"]).apply(get_season_from_date)
            existing_other_seasons = existing.loc[existing_season != current_season, df_current.columns]
            df_all = pd.concat([existing_other_seasons, df_current], ignore_index=True)

    df_all = task_compute_ewp(df_all)
    df_all = task_compute_team_power(df_all)

    # Write all features to DB — replace since we recompute everything
    con = sqlite3.connect(DB_PATH)
    df_all.to_sql("features", con, if_exists="replace", index=False)
    print(f"Features written — {len(df_all)} rows across {len(seasons)} seasons")
    con.close()

@flow(name="Training flow")
def training_flow(force_train: bool = False):
    """Load features from DB, preprocess into long format, then (re)train the model
    if it hasn't been trained in the last TRAINING_INTERVAL_DAYS days (or always, if force_train)."""
    df = task_load_features()
    df_long = task_preprocessing(df)

    Path("outputs").mkdir(exist_ok=True)
    df_long.to_csv("outputs/df_preprocessed.csv", index=False)

    days_since = task_days_since_last_training()
    if force_train or days_since is None or days_since >= TRAINING_INTERVAL_DAYS:
        train(df_long)
    else:
        print(f"Model trained {days_since} day(s) ago (< {TRAINING_INTERVAL_DAYS}) — skipping retraining")

    return df_long

@flow(name="Predictions")
def prediction_flow(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Select today matches and if exists predict xG"""
    df_selected = task_match_selection(df)
    if df_selected.empty:
        print("No match today")
        return None

    df_predicted = task_predictions(df_selected)
    df_games = task_load_games()
    rho = task_rho_estimator(df_games)
    df_predicted = task_score_matrices(df_predicted, rho)
    df_predicted = task_compute_proba(df_predicted)
    df_predicted = task_compute_score(df_predicted)
    return df_predicted

@flow(name="Save predictions")
def save_predictions_flow(df_predicted: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Persist predictions to DB and return them merged with team names for display."""
    if df_predicted is None:
        return None

    task_save_predictions(df_predicted)
    return task_display_predictions(df_predicted)

# ── Pipelines ─────────────────────────────────────────────────────────────────

@flow(name="Prono PL full pipeline")
def full_pipeline(seasons: Optional[list] = None, force_train: bool = False, force_compute: bool = False):
    """Full pipeline — scrape per season, then features + training on all."""
    if seasons is None:
        seasons = [get_current_season()]

    # 1. Setup DB once
    database_setup_flow()

    # 2. Scrape season per season
    for season in seasons:
        scraping_flow(season)

    # 3. Features on all seasons
    features_flow(force_compute=force_compute)

    # 4. Upload DB once (scrap data and features)
    database_upload_flow()

    # 5. Preprocessing + training model
    df_long = training_flow(force_train=force_train)

    # 6. Predictions
    df_predicted = prediction_flow(df_long)
    df_predictions = save_predictions_flow(df_predicted)

    # 7. Upload DB again (predictions written after step 4's upload)
    database_upload_flow()

    print(df_predictions)


if __name__ == "__main__":
    # First run
    full_pipeline(seasons=["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
                  force_train=True, force_compute=True)

    # Run daily
    # full_pipeline()
