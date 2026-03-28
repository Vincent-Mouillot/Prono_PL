from prefect import flow, task
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# Database
from database import DB_PATH, init_db, check_db_exists, download_db, upload_db

# Scrapers
from scrapers import get_calendar, get_players_stats, get_teams_stats

# Features
from features import compute_avg_goals_feature, compute_ewp_feature, compute_ranking_feature

# ML
from ml import preprocessing_function


# ── Utils ─────────────────────────────────────────────────────────────────────

def get_current_season() -> str:
    """Returns current season — if before August, returns previous year."""
    year = datetime.now().year
    month = datetime.now().month
    return str(year) if month >= 8 else str(year - 1)


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

@task(name="Compute average goals", retries=2, retry_delay_seconds=30)
def task_compute_avg_goals(df: pd.DataFrame) -> pd.DataFrame:
    return compute_avg_goals_feature(df)


# ── ML tasks ──────────────────────────────────────────────────────────────────

@task(name="Preprocess data into long format", retries=2, retry_delay_seconds=30)
def task_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    return preprocessing_function(df)


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
def features_flow():
    """Compute features for ALL seasons at once and write to features table."""
    df_games = task_load_games()
    seasons = task_load_seasons()

    # Compute ranking per season then concatenate
    df_all = pd.concat([
        task_compute_ranking(df_games, str(season)) for season in seasons
    ], ignore_index=True)

    df_all = task_compute_avg_goals(df_all)
    df_all = task_compute_ewp(df_all)

    # Write all features to DB — replace since we recompute everything
    con = sqlite3.connect(DB_PATH)
    df_all.to_sql("features", con, if_exists="replace", index=False)
    print(f"Features written — {len(df_all)} rows across {len(seasons)} seasons")
    con.close()

@flow(name="Training flow")
def training_flow():
    """Load features from DB and preprocess into long format."""
    df = task_load_features()
    df_long = task_preprocessing(df)

    Path("outputs").mkdir(exist_ok=True)
    df_long.to_csv("outputs/df_preprocessed.csv", index=False)
    return df_long


# ── Pipelines ─────────────────────────────────────────────────────────────────

@flow(name="Feature pipeline")
def pipeline(season: Optional[str] = None):
    """Scrape data for a single season and upload DB."""
    if season is None:
        season = get_current_season()
    print(f"Running scraping pipeline for season {season}")

    database_setup_flow()
    scraping_flow(season)
    database_upload_flow()

@flow(name="ML pipeline")
def ml_pipeline():
    """Compute features on all seasons, then preprocess and train."""
    features_flow()
    training_flow()

@flow(name="Prono PL full pipeline")
def full_pipeline(seasons: Optional[list] = None):
    """Full pipeline — scrape per season, then features + training on all."""
    if seasons is None:
        seasons = [get_current_season()]

    # 1. Scrape saison par saison
    for season in seasons:
        pipeline(season=season)

    # 2. Features + training sur toutes les saisons combinées
    ml_pipeline()


if __name__ == "__main__":
    # Premier run historique
    full_pipeline(seasons=["2021", "2022", "2023", "2024", "2025"])

    # Run quotidien automatique
    # full_pipeline()
