library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(lubridate)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_cloud_db.R"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, 
                      "SELECT Id, Abv FROM Table_teams WHERE Comp = 'Premier League';")

dbDisconnect(con)

source(file.path(root, "Prono_PL", "compute_match_pred.R"))

data <- data %>% 
  left_join(df_team,
            by=c("H_team" = "Id")) %>% 
  left_join(df_team,
            by=c("A_team" = "Id"),
            suffix = c("_h", "_a"))

if(nrow(data) != 0){
  source(file.path(root, "Prono_PL", "store_history.R")) 
}

# Ré-uploader et remplacer l'ancien fichier sur Google Drive
drive_update(file, media = temp_db_path)

# Fonction pour afficher le tableau dans le format souhaité
print_table <- function(df) {
  
  df <- df %>% 
    filter(ymd(Date) - today() == 0)
  
  if(nrow(df) != 0){
    output <- paste0(data$Date %>% unique(), "\n")
    
    for (i in 1:nrow(df)) {
      output <- paste0(output, sprintf("| %-4s | %-3s | %-3s | %-3s | %-3s | %-3s | %-3s | %-3s |\n", 
                                       df$Time[i],
                                       df$Abv_h[i], 
                                       paste0(df$`H(%)`[i], "%"), 
                                       paste0(df$`D(%)`[i], "%"), 
                                       paste0(df$`A(%)`[i], "%"), 
                                       df$Abv_a[i], 
                                       df$score_pred[i], 
                                       paste0(df$`score_pred_%`[i], "%")))
    }
  }else{
    output <- "No match to predict today"
  }
  
  return(output)
}

# Afficher le tableau
output_table <- print_table(data)

cat(output_table)

# Écrire la sortie dans un fichier texte pour la récupérer dans le script bash
writeLines(output_table,  file.path(root, "Prono_PL","table_output.txt"))

# Optionnel : Supprimer le fichier temporaire après usage
file.remove(temp_db_path)