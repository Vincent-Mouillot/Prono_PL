library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_cloud_db.R"))

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

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

# Fonction pour afficher le tableau dans le format souhaité
print_table <- function(df) {
  # Stocker la sortie dans une variable
  output <- ""
  output <- paste0(output, "--------------------------------------------------------\n")
  output <- paste0(output, "| Home | H(%)  | D(%)  | A(%)  | Away | Score | Sc (%) |\n")
  output <- paste0(output, "|------|-------|-------|-------|------|-------|--------|\n")
  
  for (i in 1:nrow(df)) {
    output <- paste0(output, sprintf("| %-4s | %-5s | %-5s | %-5s | %-4s |  %-4s | %-6s |\n", 
                                     df$Abv_h[i], df$`H(%)`[i], df$`D(%)`[i], df$`A(%)`[i], df$Abv_a[i], df$score_pred[i], df$`score_pred_%`[i]))
  }
  
  output <- paste0(output, "--------------------------------------------------------\n")
  return(output)
}

# Afficher le tableau
output_table <- print_table(data)

cat(output_table)

# Écrire la sortie dans un fichier texte pour la récupérer dans le script bash
writeLines(output_table, "table_output.txt")
