library(DBI)
library(RSQLite)
library(tidyverse)
library(ggplot2)
library(factoextra)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, 
                      "SELECT * FROM Table_teams WHERE Comp = 'Premier League';")

df_stats <- dbGetQuery(con, 
                            "SELECT * FROM Stats_players;")

dbDisconnect(con)

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
    across(everything(), mean, na.rm = TRUE) %>% 
      round(2)
  )
  
data_clustering <- df_stats_agg %>% 
  select(-team) %>%
  na.omit()

data_clustering <- data_clustering %>% 
  select(Pass_Completion_Perc, 
         npxG_NonPenalty_xG,
         xAG_Exp_Assisted_Goals,
         Ball_Recoveries,
         Perc_of_Aerials_Won
         )

data_scaled <- scale(data_clustering)

set.seed(42)
kmeans_result <- kmeans(data_scaled, centers = 3, nstart = 25)

df_stats_agg$cluster <- kmeans_result$cluster

fviz_cluster(kmeans_result, data = data_scaled)