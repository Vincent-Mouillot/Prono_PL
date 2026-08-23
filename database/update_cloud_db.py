from googleapiclient.http import MediaFileUpload
from database.get_cloud_db import drive_service, DB_PATH, DB_NAME, DRIVE_FOLDER_ID


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
        file_metadata = {
            "name": DB_NAME,
            "parents": [DRIVE_FOLDER_ID]
        }
        drive_service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()
        print(f"'{DB_NAME}' created on Google Drive.")