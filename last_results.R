library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_calendrier <- dbGetQuery(con, 
                            "SELECT * FROM Calendrier WHERE result IS NOT NULL;")

dbDisconnect(con)


last_results_function <- function(df, side = NA_character_, nb_match = 3) {
  df_result <- df %>%
    filter(!is.na(result)) %>% 
    select(Wk, Home = Home_id, Away = Away_id, result) %>%
    pivot_longer(
      cols = c(Home, Away),
      names_to = "Side",
      values_to = "Team_id"
    ) %>%
    mutate(Result_team = case_when(((result == "H") &
                                      (Side == "Home")) | 
                                    ((result == "A") & 
                                      (Side == "Away")) ~ "W", 
                                   ((result == "H") &
                                      (Side == "Away")) | 
                                     ((result == "A") & 
                                      (Side == "Home")) ~ "L", 
                                   .default = "D"))
  
  if (side %in% c("Home", "Away")) {
    df_result <- df_result %>%
      filter(Side == side)
  }
  
  res <- df_result %>%
    group_by(Team_id) %>%
    slice_tail(n = nb_match) %>%
    arrange(desc(Wk)) %>%
    mutate(J_label = paste0("J-", row_number())) %>%
    select(Team_id, Result_team, J_label) %>%
    pivot_wider(names_from = J_label, values_from = Result_team) %>%
    rename_with( ~ if (is.na(side) ||
                       side == "") {
      .x
    } else {
      paste0(.x, "_", side)
    }, -Team_id)
  
  return(res)
}