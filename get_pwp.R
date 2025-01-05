library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(zoo)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_xpg_team <- dbGetQuery(
  con,
  "SELECT team,
          game,
          SUM(npxG_NonPenalty_xG) AS xG
  FROM Stats_players
  GROUP BY team, game;"
)


dbDisconnect(con)

compute_pwp <- function(calendrier, stats, side = NA_character_) {
  df <- calendrier %>%
    filter(!is.na(result)) %>% 
    select(Wk,
           id,
           Home_id,
           Away_id) %>% 
    left_join(stats, 
              by = c(
                "id" = "game", 
                "Home_id" = "team"
              )
    ) %>%
    left_join(stats, 
              by = c(
                "id" = "game", 
                "Away_id" = "team"
              ), 
              suffix = c("_h", "_a")
    )
  
  test <<- df
  
  if (!is.na(side) && side %in% c("Home_id", "Away_id")) {
    xG_for_col <- if (side == "Home_id") "xG_h" else "xG_a"
    xG_against_col <- if (side == "Home_id") "xG_a" else "xG_h"
    
    df_pwp_side <- df %>%
      select(
        Wk,
        team = !!sym(side),
        xG_for = !!sym(xG_for_col),
        xG_against = !!sym(xG_against_col)
      )
  } else {
    df_pwp_side <- df %>%
      select(
        Wk,
        team = Home_id,
        xG_for = xG_h,
        xG_against = xG_a
      ) %>%
      bind_rows(
        df %>%
          select(
            Wk,
            team = Away_id,
            xG_for = xG_a,
            xG_against = xG_h
          )
      )
  }
  
  df_pwp <- df_pwp_side %>%
    group_by(team) %>%
    mutate(
      cum_xG_for = cumsum(xG_for),
      cum_xG_against = cumsum(xG_against),
      pwp = cum_xG_for^2 / (cum_xG_for^2 + cum_xG_against^2),
      Wk = Wk + 1
    ) %>%
    ungroup() %>%
    select(
      Wk,
      team,
      pwp
    )
  
  # Add a row for the first matchday with pwp = 0.5
  unique_teams <- unique(df_pwp$team)
  all_wk <- c(1, unique(df_pwp$Wk))
  df <- expand.grid(team = unique_teams, Wk = all_wk)
  
  df <- df %>% 
    left_join(df_pwp,
              by = c("team", "Wk")) %>%
    arrange(team, Wk) %>% 
    group_by(team) %>% 
    mutate(pwp = if_else(Wk == 1,
                         0.5,
                         pwp),
           pwp = na.locf(pwp))
  test <<- df
  pwp_suffix <- case_when(
    !is.na(side) & side == "Home_id" ~ "_h",
    !is.na(side) & side == "Away_id" ~ "_a",
    TRUE ~ ""
  )
  
  df <- df %>%
    rename_with(~ paste0("pwp", pwp_suffix), .cols = "pwp") %>% 
    mutate(Wk = as.integer(Wk))
  
  return(df)
}