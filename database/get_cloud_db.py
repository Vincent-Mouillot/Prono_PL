import os
import io
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# ── Auth setup ────────────────────────────────────────────────────────────────

load_dotenv()
PERSONAL_EMAIL = os.environ.get("PERSONAL_EMAIL")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")

if os.name == "nt":  # Windows
    service_account_root = "C:/Users/vmoui/Documents/api_keys/"
else:
    service_account_root = "/home/vmouillot/Documents/api_keys/"

service_account_json = next(
    (os.path.join(service_account_root, f) for f in os.listdir(service_account_root) if f.endswith(".json")),
    None
)

if not service_account_json:
    raise FileNotFoundError(f"No JSON file found in {service_account_root}")

# drive_service instantiated once at module load — reused by all functions
credentials = Credentials.from_service_account_file(service_account_json)
drive_service = build("drive", "v3", credentials=credentials)

# ── Root detection ────────────────────────────────────────────────────────────

root = Path(__file__).resolve().parent
while not (root / "Prono_PL").exists() and root != root.parent:
    root = root.parent

if not (root / "Prono_PL").exists():
    raise FileNotFoundError("Prono_PL directory not found")

project_root = root / "Prono_PL"
DB_NAME = "understats_database.db"
DB_PATH = project_root / DB_NAME

# ── Functions ─────────────────────────────────────────────────────────────────

def check_db_exists() -> bool:
    """Check if the DB file exists in the project folder on Google Drive."""
    results = drive_service.files().list(
        q=f"name='{DB_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
        fields="files(id, name)"
    ).execute()
    return len(results.get("files", [])) > 0


def download_db():
    """Download the DB from Google Drive to the project root."""
    results = drive_service.files().list(
        q=f"name='{DB_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
        fields="files(id, name)"
    ).execute()
    items = results.get("files", [])

    if not items:
        raise FileNotFoundError(f"'{DB_NAME}' not found in Drive folder {DRIVE_FOLDER_ID}")

    file_id = items[0]["id"]
    print(f"File found: https://drive.google.com/file/d/{file_id}/view")

    os.makedirs(DB_PATH.parent, exist_ok=True)

    request = drive_service.files().get_media(fileId=file_id)
    with open(DB_PATH, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")

    print(f"DB downloaded to: {DB_PATH}")


def upload_db():
    """Upload the local DB to Google Drive, replacing the existing file."""
    results = drive_service.files().list(
        q=f"name='{DB_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
        fields="files(id, name)"
    ).execute()
    items = results.get("files", [])

    media = MediaFileUpload(DB_PATH, resumable=True)

    if items:
        file_id = items[0]["id"]
        drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"'{DB_NAME}' updated on Google Drive.")
    else:
        file_metadata = {"name": DB_NAME, "parents": [DRIVE_FOLDER_ID]}
        drive_service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()
        print(f"'{DB_NAME}' created on Google Drive.")