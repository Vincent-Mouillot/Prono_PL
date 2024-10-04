library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_classement <- dbGetQuery(con, 
                      "SELECT * FROM Classement;")

df_calendrier <- dbGetQuery(con, 
                            "SELECT * FROM Calendrier;")

dbDisconnect(con)

compute_diff_class <- function(df_calendrier, df_classement){
  df_calendrier <- df_calendrier %>% 
    mutate(Wk_1 = paste0("J", Wk - 1)) %>% 
    left_join(
      df_classement %>% 
        pivot_longer(
          cols = starts_with("J"),
          names_to = "Wk_1",
          values_to = "Class"
        ),
      by = c("Home_id" = "Id","Wk_1")
    ) %>% 
    left_join(
      df_classement %>% 
        pivot_longer(
          cols = starts_with("J"),
          names_to = "Wk_1",
          values_to = "Class"
        ),
      by = c("Away_id" = "Id","Wk_1"),
      suffix = c("_home", "_away")
    ) %>% 
    mutate(diff_class_h = Class_home - Class_away,
           diff_class_a = Class_away - Class_home) %>% 
    select(-c(Wk_1, Class_home, Class_away))
  
  return(df_calendrier)
}
