df_prono <- data %>% 
  select(Date, H_team, `H(%)`, `D(%)`, `A(%)`, A_team, score_pred, `score_pred_%`)

# Connexion à la base de données SQLite
con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

# Création de la table history si elle n'existe pas
dbExecute(con, "
  CREATE TABLE IF NOT EXISTS Prono_history (
    Date TEXT,
    H_team TEXT,
    A_team TEXT,
    H_percent REAL,
    D_percent REAL,
    A_percent REAL,
    score_pred TEXT,
    score_pred_percent REAL,
    PRIMARY KEY (Date, H_team, A_team)
  );
")

# Fonction pour insérer ou mettre à jour les données dans la table history
insert_or_update_history <- function(df_prono, con) {
  
  for (i in 1:nrow(df_prono)) {
    # Extraction des valeurs d'une ligne du dataframe
    date <- df_prono$Date[i]
    h_team <- df_prono$H_team[i]
    a_team <- df_prono$A_team[i]
    h_percent <- df_prono$`H(%)`[i]
    d_percent <- df_prono$`D(%)`[i]
    a_percent <- df_prono$`A(%)`[i]
    score_pred <- df_prono$score_pred[i]
    score_pred_percent <- df_prono$`score_pred_%`[i]
    
    # Vérifier si la combinaison existe déjà avec une requête paramétrée
    query <- dbGetQuery(con, "
      SELECT COUNT(*) AS count FROM Prono_history
      WHERE Date = ? AND H_team = ? AND A_team = ?", 
                        params = list(date, h_team, a_team)
    )
    
    if (query$count == 0) {
      # Si la combinaison n'existe pas, on insère les données (requête paramétrée)
      dbExecute(con, "
        INSERT INTO Prono_history (Date, H_team, A_team, H_percent, D_percent, A_percent, score_pred, score_pred_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                params = list(date, h_team, a_team, h_percent, d_percent, a_percent, score_pred, score_pred_percent)
      )
    } else {
      # Si la combinaison existe, on met à jour les autres colonnes (requête paramétrée)
      dbExecute(con, "
        UPDATE Prono_history
        SET H_percent = ?, D_percent = ?, A_percent = ?, score_pred = ?, score_pred_percent = ?
        WHERE Date = ? AND H_team = ? AND A_team = ?", 
                params = list(h_percent, d_percent, a_percent, score_pred, score_pred_percent, date, h_team, a_team)
      )
    }
  }
}

# Appel de la fonction pour insérer ou mettre à jour les données
insert_or_update_history(df_prono, con)

# Déconnexion de la base de données
dbDisconnect(con)
