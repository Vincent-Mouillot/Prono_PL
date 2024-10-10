library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_distance.R"))
source(file.path(root, "Prono_PL", "get_diff_class.R"))
source(file.path(root, "Prono_PL", "compute_last_results.R"))
source(file.path(root, "Prono_PL", "compute_avg_gls.R"))

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
df_serie <- get_last_results_all_weeks(df_calendrier, nb_match = 1)
df_home_serie <- get_last_results_all_weeks(df_calendrier, "Home", nb_match = 1)
df_away_serie <- get_last_results_all_weeks(df_calendrier, "Away", nb_match = 1)


df_long <- df_calendrier %>% 
  # Première transformation pour les équipes à domicile
  select(Wk, Date, Day, Time, Team_id = Home_id, Team = Home, Opponent_id = Away_id, Opponent = Away, Diff_clas = diff_class_h, Score = score_home, Score_opp = score_away) %>%
  mutate(Dist = 0) %>%
  select(Wk, Date, Day, Time, Team_id, Team, Opponent_id, Opponent, Diff_clas, Dist, Score, Score_opp) %>% 
  left_join(df_home_serie,
            by = c("Team_id", "Wk")) %>% 
  rename("J-1_Side" = `J-1_Home`) %>% 
  bind_rows(
    # Deuxième transformation pour les équipes à l'extérieur
    df_calendrier %>%
      select(Wk, Date, Day, Time, Team_id = Away_id, Team = Away, Opponent_id = Home_id, Opponent = Home, Diff_clas = diff_class_a, Dist = dist_away_norm, Score = score_away, Score_opp = score_home) %>% 
      left_join(df_away_serie,
                by = c("Team_id", "Wk")) %>% 
      rename("J-1_Side" = `J-1_Away`)
  ) %>%
  arrange(Wk, Date) %>% 
  mutate(`J-1_Side` = replace_na(`J-1_Side`, "D"))

# Affichage du DataFrame transformé
df <- df_long %>% 
  calculate_previous_week_avg("Score", "Team_id") %>% 
  calculate_previous_week_avg("Score_opp", "Opponent_id") %>% 
  left_join(df_serie,
            by = c("Team_id", "Wk")) %>% 
  mutate(`J-1` = replace_na(`J-1`, "D"))

encoded_df <- df #cbind(df[, !names(df) %in% c("Day", "Time")], model.matrix(~ Day + Time - 1, data = df))