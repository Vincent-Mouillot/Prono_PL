library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

source("get_distance.R")
source("get_diff_class.R")

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, 
                      "SELECT * FROM Table_teams WHERE Comp = 'Premier League';")

df_classement <- dbGetQuery(con, 
                            "SELECT * FROM Classement;")

df_calendrier <- dbGetQuery(con, 
                            "SELECT * FROM Calendrier;")

dbDisconnect(con)

df_calendrier <- compute_distance(df_calendrier, df_team)
df_calendrier <- compute_diff_class(df_calendrier, df_classement)


df_long <- df_calendrier %>% 
  # Première transformation pour les équipes à domicile
  select(Wk, Date, Day, Time, Team_id = Home_id, Team = Home, Opponent_id = Away_id, Opponent = Away, Diff_clas = diff_class_h, Score = score_home) %>%
  mutate(Dist = 0) %>%
  select(Wk, Date, Day, Time, Team_id, Team, Opponent_id, Opponent, Diff_clas, Dist, Score) %>% 
  bind_rows(
    # Deuxième transformation pour les équipes à l'extérieur
    df_calendrier %>%
      select(Wk, Date, Day, Time, Team_id = Away_id, Team = Away, Opponent_id = Home_id, Opponent = Home, Diff_clas = diff_class_a, Dist = dist_away, Score = score_away) 
  ) %>%
  arrange(Wk, Date)

# Affichage du DataFrame transformé
df <- df_long %>% 
  select(Day, Time, Diff_clas, Dist, Score)

encoded_df <- cbind(df[, !names(df) %in% c("Day", "Time")], model.matrix(~ Day + Time - 1, data = df))

# Affichage du résultat
print(encoded_df)