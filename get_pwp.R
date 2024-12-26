library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_stat <- dbGetQuery(con,
                      "SELECT team, game, SUM(npxG_NonPenalty_xG) AS xG FROM Stats_players GROUP BY team, game;")

df_calendrier <- dbGetQuery(con,
                            "SELECT Wk, id, Home_id, Away_id FROM Calendrier WHERE result IS NOT NULL;")


dbDisconnect(con)

test <- df_calendrier %>% 
  left_join(df_stat, 
            by=c('id' = 'game', 'Home_id' = 'team')) %>% 
  left_join(df_stat, 
            by=c('id' = 'game', 'Away_id' = 'team'), suffix = c("_h", "_a")) %>% 
  select(Wk, team = Home_id, xG_for = xG_h, xG_against = xG_a) %>% 
  bind_rows(df_calendrier %>% 
              left_join(df_stat, 
                        by=c('id' = 'game', 'Home_id' = 'team')) %>% 
              left_join(df_stat, 
                        by=c('id' = 'game', 'Away_id' = 'team'), suffix = c("_h", "_a")) %>% 
              select(Wk, team = Away_id, xG_for = xG_a, xG_against = xG_h) 
            ) %>% 
  group_by(team) %>% 
  arrange(Wk, .by_group = TRUE) %>% 
  mutate(cum_xG_for = cumsum(xG_for),
         cum_xG_against = cumsum(xG_against))
