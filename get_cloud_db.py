import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from pathlib import Path

# Détection du système d'exploitation
if os.name == "nt":  # Windows
    service_account_root = "C:/Users/vmoui/Documents/api_keys/"
else:
    service_account_root = "/home/vmouillot/Documents/api_keys/"

# Récupération du fichier JSON du compte de service
service_account_json = next(
    (os.path.join(service_account_root, file) for file in os.listdir(service_account_root) if file.endswith(".json")),
    None
)

if not service_account_json:
    raise FileNotFoundError(f"Aucun fichier JSON trouvé dans {service_account_root}")

# Trouver le répertoire racine contenant "Prono_PL" et créer le chemin vers le fichier SQLite
root = Path(__file__).resolve().parent  # Partir du répertoire actuel du script

# Remonter dans les répertoires jusqu'à ce que l'on trouve "Prono_PL"
while not (root / 'Prono_PL').exists() and root != root.parent:
    root = root.parent

# Vérification et création du chemin du fichier SQLite
if (root / 'Prono_PL').exists():
    project_root = root / 'Prono_PL'
else:
    print("Répertoire 'Prono_PL' non trouvé")

# Authentification avec le compte de service
credentials = Credentials.from_service_account_file(service_account_json)
drive_service = build("drive", "v3", credentials=credentials)

# Exemple: Télécharger un fichier
file_name = "my_database.db"

# Rechercher le fichier dans Google Drive
results = drive_service.files().list(q=f"name='{file_name}'", fields="files(id, name)").execute()
items = results.get("files", [])

if not items:
    raise FileNotFoundError(f"Fichier '{file_name}' introuvable sur Google Drive")

file_id = items[0]["id"]

# Chemin temporaire pour le fichier téléchargé
temp_db_path = os.path.join(project_root, "my_database.db")

# Créer le dossier cible si nécessaire
os.makedirs(os.path.dirname(temp_db_path), exist_ok=True)

# Télécharger le fichier
request = drive_service.files().get_media(fileId=file_id)
with open(temp_db_path, "wb") as file:
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Téléchargement {int(status.progress() * 100)}%.")

print(f"Fichier téléchargé dans : {temp_db_path}")