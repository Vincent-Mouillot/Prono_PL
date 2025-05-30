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
file <- drive_get("my_database_l1.db")

# Télécharger le fichier .db dans un dossier temporaire
temp_db_path <- file.path(root, "Prono_PL", "my_database_l1.db")
drive_download(file, path = temp_db_path, overwrite = TRUE)