if (!requireNamespace("rprojroot", quietly = TRUE)) {
  install.packages("rprojroot")
}

library(rprojroot)
library(googledrive)
library(gargle)

if (.Platform$OS.type == "windows") {
  service_account_root <- "C:/Users/vmoui/Documents/api_keys/"
} else {
  service_account_root <- "/home/vmouillot/Documents/api_keys/"
}

service_account_json <<- list.files(service_account_root, full.names = TRUE)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

# Authentification avec le compte de service
drive_auth(path = service_account_json)

# Exemple: Télécharger un fichier
file <- drive_get("my_database.db")

# Télécharger le fichier .db dans un dossier temporaire
temp_db_path <- file.path(root, "Prono_PL", "my_database.db")
drive_download(file, path = temp_db_path, overwrite = TRUE)

#script pour telecharger la table et enregistrer une table temp

source(file.path(root, "Prono_PL", "get_calendrier.R"))

source(file.path(root, "Prono_PL", "get_all_data.R"))

source(file.path(root, "Prono_PL", "get_classement.R"))

# Ré-uploader et remplacer l'ancien fichier sur Google Drive
drive_update(file, media = temp_db_path)

# Optionnel : Supprimer le fichier temporaire après usage
file.remove(temp_db_path)