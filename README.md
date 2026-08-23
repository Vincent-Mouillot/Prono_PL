# Prono_PL

Premier League match prediction pipeline. Scrapes Understat data, builds features (ranking, EWP, offensive/defensive power), trains an xG model, then predicts upcoming match scores with a Dixon-Coles model.

## Architecture

The pipeline is orchestrated with [Prefect](https://www.prefect.io/) (`pipeline.py`), organized into sub-flows:

1. **Database setup** — downloads the SQLite DB from Google Drive, or initializes it if it doesn't exist.
2. **Scraping** — fetches calendar, team stats and player stats from [Understat](https://understat.com/) (`scrapers/`).
3. **Features** — computes ranking, EWP (expected win probability) and offensive/defensive power per team (`features/`).
4. **Database upload** — syncs the DB back to Google Drive.
5. **Training** — preprocesses features and (re)trains the xG model if needed (`ml/`), tracked via MLflow.
6. **Predictions** — selects today's matches, predicts xG, applies the Dixon-Coles correction and computes 1X2 probabilities + most likely score.
7. **Save predictions** — persists predictions to DB and syncs to Drive again.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # or source .venv/bin/activate on Linux
pip install -r requirements.txt
```

Create a `.env` file at the project root with:

```
SERVICE_ACCOUNT_JSON=<path to the Google service account credentials file>
PERSONAL_EMAIL=<email>
DRIVE_FOLDER_ID=<Google Drive folder id>
```

## Running the pipeline

```bash
python pipeline.py
```

The daily run (`full_pipeline()`) does an incremental run (features recomputed for the current season only, model retrained only if older than 30 days). The first run / full backfill needs `force_train=True, force_compute=True` with the list of all seasons.

## Automated deployment (Raspberry Pi)

The pipeline runs via a plain cron job, no Prefect server needed:

```
0 8 * * * /home/pi/Prono_PL/run_pipeline.sh
```

where `run_pipeline.sh` activates the venv and runs `python pipeline.py`, logging its output.

## `old/` — not yet ported

Leftover scripts from the pre-refactor R/Selenium version, covering functionality the Python pipeline doesn't reimplement yet:

- **`compute_brier_score.R`** — computes the Brier score of predicted 1X2 probabilities against actual results, to evaluate model calibration over time.
- **`get_proba_book.R`** — scrapes bookmaker odds (compare-bet.fr), converts them to implied probabilities and stores them in a `Book_history` table, to compare against the model's own predictions.
- **`get_win_proba_opta.py`** — scrapes Opta's win probabilities via Selenium.

None of these are wired into `pipeline.py` yet — they're kept as reference for whoever picks up the calibration-tracking / odds-comparison work.
