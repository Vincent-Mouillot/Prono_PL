from prefect import flow, task
import pandas as pd
import sqlite3

# Database
from database import DB_PATH, init_db, check_db_exists, download_db, upload_db

# Scrapers
from scrapers import get_calendar, get_players_stats, get_teams_stats

#Features
from features import compute_avg_goals_feature, compute_ewp_feature, compute_ranking_feature

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

@task(name="Scrape calendrier", retries=2, retry_delay_seconds=30)
def task_get_calendar():
    get_calendar()

@task(name="Scrape teams tats", retries=2, retry_delay_seconds=30)
def task_get_teams_stats():
    get_teams_stats()

@task(name="Scrape players stats", retries=2, retry_delay_seconds=30)
def task_get_players_stats():
    get_players_stats()


# ── Load games ────────────────────────────────────────────────────────────────

@task(name="Load games from DB")
def task_load_games() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM games;", con)
    con.close()
    return df


# ── Features tasks ────────────────────────────────────────────────────────────

@task(name="Compute Ranking difference", retries=2, retry_delay_seconds=30)
def task_compute_ranking(df_calendar: pd.DataFrame):
    return compute_ranking_feature(df_calendar)

@task(name="Compute EWP", retries=2, retry_delay_seconds=30)
def task_compute_ewp(df_calendar: pd.DataFrame):
    return compute_ewp_feature(df_calendar)

@task(name="Compute average goal", retries=2, retry_delay_seconds=30)
def task_compute_avg_goals(df_calendar: pd.DataFrame):
    return compute_avg_goals_feature(df_calendar)


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
def scraping_flow():
    """Scrape all data sources — each task is independent and can be retried."""
    task_get_calendar()
    task_get_players_stats()
    task_get_teams_stats()

@flow(name="Database upload flow")
def database_upload_flow():
    """Upload the updated DB back to Google Drive."""
    task_upload_db()

@flow(name="Compute features")
def features_flow():
    """Load the games df and add the features"""
    df_calendar = task_load_games()
    df_calendar = task_compute_ranking(df_calendar)
    df_calendar = task_compute_avg_goals(df_calendar)
    df_calendar = task_compute_ewp(df_calendar)
    return df_calendar


# ── Main pipeline ─────────────────────────────────────────────────────────────

@flow(name="Prono PL pipeline")
def pipeline():
    database_setup_flow()           # download or init DB
    scraping_flow()                 # scrape all data sources
    database_upload_flow()          # upload updated DB to Drive
    df_calendar = features_flow()   # compute ranking feature
    print(df_calendar.head(20))
    print(df_calendar.columns)


if __name__ == "__main__":
    pipeline()