library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_distance.R"))
source(file.path(root, "Prono_PL", "get_diff_class.R"))
# source(file.path(root, "Prono_PL", "compute_last_results.R"))
source(file.path(root, "Prono_PL", "compute_nb_points_last_weeks.R"))
source(file.path(root, "Prono_PL", "compute_avg_gls.R"))
source(file.path(root, "Prono_PL", "compute_kmeans_team.R"))
source(file.path(root, "Prono_PL", "get_pwp.R"))


do_preprocessing <- function(database){
  sqlite_file <- file.path(root, "Prono_PL", database)
  
  con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)
  
  df_team <- dbGetQuery(con, 
                        "SELECT * FROM Table_teams WHERE Comp = 'Premier League';")
  
  df_classement <- dbGetQuery(con, 
                              "SELECT * FROM Classement;")
  
  df_calendrier <- dbGetQuery(con, 
                              "SELECT * FROM Calendrier;")
  
  dbDisconnect(con)
  
  df_stats_agg <- compute_kmeans_team(sqlite_file = database, k = 3)
  
  df_calendrier <- compute_distance(df_calendrier, df_team)
  df_calendrier <- compute_diff_class(df_calendrier, df_classement)
  # df_serie <- get_last_results_all_weeks(df_calendrier, nb_match = 3)
  # df_home_serie <- get_last_results_all_weeks(df_calendrier, "Home", nb_match = 2)
  # df_away_serie <- get_last_results_all_weeks(df_calendrier, "Away", nb_match = 2)
  df_serie <- get_nb_points_all_weeks(df_calendrier, nb_match = 3)
  df_home_serie <- get_nb_points_all_weeks(df_calendrier, "Home", nb_match = 3)
  df_away_serie <- get_nb_points_all_weeks(df_calendrier, "Away", nb_match = 3)
  df_pwp <- compute_pwp(df_calendrier, df_xpg_team)
  
  df_long <- df_calendrier %>% 
    left_join(df_home_serie, by = c("Home_id" = "Team_id", "Wk")) %>% 
    # Première transformation pour les équipes à domicile
    select(Wk, Date, Day, Time, Team_id = Home_id, Team = Home, Opponent_id = Away_id, Opponent = Away, Diff_clas = diff_class_h, Nb_point_side = nb_point_Home, Score = score_home, Score_opp = score_away) %>%
    mutate(Dist = 0) %>%
    select(Wk, Date, Day, Time, Team_id, Team, Opponent_id, Opponent, Diff_clas, Dist, Nb_point_side, Score, Score_opp) %>% 
    bind_rows(
      # Deuxième transformation pour les équipes à l'extérieur
      df_calendrier %>%
        left_join(df_away_serie, by = c("Away_id" = "Team_id", "Wk")) %>% 
        select(Wk, Date, Day, Time, Team_id = Away_id, Team = Away, Opponent_id = Home_id, Opponent = Home, Diff_clas = diff_class_a, Dist = dist_away_norm, Nb_point_side = nb_point_Away, Score = score_away, Score_opp = score_home)
    ) %>%
    arrange(Wk, Date)
  
  # Affichage du DataFrame transformé
  df <- df_long %>% 
    calculate_previous_week_avg("Score", "Team_id") %>% 
    calculate_previous_week_avg("Score_opp", "Opponent_id") %>% 
    left_join(df_serie,
              by = c("Team_id", "Wk")) %>% 
    mutate(across(starts_with("nb_point"), ~ replace_na(.x, 3))) %>% 
    left_join(
      df_stats_agg %>% 
        select(team,
               cluster),
      by = c("Team_id" = "team")
    ) %>% 
    left_join(
      df_stats_agg %>% 
        select(team,
               cluster),
      by = c("Opponent_id" = "team"),
      suffix = c("", "_opp")
    ) %>% 
    left_join(df_pwp,
              by = c("Team_id" = "team", "Wk")) %>%
    left_join(df_pwp,
              by = c("Opponent_id" = "team", "Wk"),
              suffix = c("", "_opp")) %>%
    mutate(cluster = na.fill(cluster, 1),
           cluster_opp = na.fill(cluster_opp, 1),
           cluster = as.factor(cluster),
           cluster_opp = as.factor(cluster_opp))
  
  encoded_df <- df
  
  return(encoded_df)
}

encoded_df <- bind_rows(
  do_preprocessing("my_database_2024_2025.db"),
  do_preprocessing("my_database.db")
) 