if (!requireNamespace("rprojroot", quietly = TRUE)) {
  install.packages("rprojroot")
}
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_cloud_db.R"))

#script pour telecharger la table et enregistrer une table temp

source(file.path(root, "Prono_PL", "get_calendrier.R"))

source(file.path(root, "Prono_PL", "get_all_data.R"))

source(file.path(root, "Prono_PL", "get_classement.R"))

# Ré-uploader et remplacer l'ancien fichier sur Google Drive
drive_update(file, media = temp_db_path)

# Optionnel : Supprimer le fichier temporaire après usage
file.remove(temp_db_path)