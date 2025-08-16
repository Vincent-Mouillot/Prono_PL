compute_kmeans_team <- function(sqlite_file, k = 3, columns_to_use = c(
  "Pass_Completion_Perc", 
  "npxG_NonPenalty_xG",
  "xAG_Exp_Assisted_Goals",
  "Ball_Recoveries",
  "Perc_of_Aerials_Won")) {
  
  library(DBI)
  library(RSQLite)
  library(tidyverse)
  library(ggplot2)
  library(factoextra)
  
  con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)
  
  df_team <- dbGetQuery(con, 
                        "SELECT * FROM Table_teams WHERE Comp = 'Premier League';")
  
  df_stats <- dbGetQuery(con, "SELECT * FROM Stats_players;")
  
  dbDisconnect(con)
  
  if(nrow(df_stats) > 300){ #300=20*15 (~nb players played after 1 Gameweek)
    
    df_stats_agg <- df_stats %>%
      group_by(team, game) %>%
      select(-c(Player, Shirt_Number, Nation, Position, Age, Minutes)) %>%
      summarise(
        across(contains("Perc"), mean, na.rm = TRUE),
        across(-contains("Perc"), sum, na.rm = TRUE)
      ) %>% 
      ungroup() %>% 
      group_by(team) %>% 
      select(-game) %>% 
      summarise(
        across(everything(), ~ round(mean(.x, na.rm = TRUE), 2))
      )
    
    data_clustering <- df_stats_agg %>% 
      select(all_of(columns_to_use)) %>%
      na.omit()
    
    data_scaled <- scale(data_clustering)
    
    set.seed(42)
    kmeans_result <- kmeans(data_scaled, centers = k, nstart = 25)
    
    df_stats_agg$cluster <- kmeans_result$cluster
    
    fviz_cluster(kmeans_result, data = data_scaled)
    
  } else {
    df_stats_agg <- df_team %>% 
      select(Id) %>% 
      rename("team" = "Id") %>% 
      mutate(cluster = 1)
  }
  
  return(df_stats_agg)
}
