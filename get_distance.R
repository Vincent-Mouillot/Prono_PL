library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(geosphere)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, 
                            "SELECT * FROM Table_teams WHERE Comp = 'Premier League';")

df_calendrier <- dbGetQuery(con, 
                             "SELECT * FROM Calendrier;")

dbDisconnect(con)

df_dist <- df_calendrier %>% 
  select(Home_id, Away_id) %>% 
  left_join(df_team %>% 
              select(Id, latitude, longitude),
            by = c("Home_id" = "Id")
            ) %>% 
  left_join(df_team %>% 
              select(Id, latitude, longitude),
            by = c("Away_id" = "Id"),
            suffix = c("_home", "_away")) %>% 
  mutate(dist_away = distHaversine(cbind(longitude_home, latitude_home), 
                              cbind(longitude_away, latitude_away)) / 1000) %>% 
  select(Home_id, Away_id, dist_away)
