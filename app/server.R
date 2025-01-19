library(shiny)
library(tidyverse)
library(DT)
library(DBI)
library(RSQLite)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, "SELECT * FROM Table_teams
                      WHERE Comp = 'Premier League';")

df_prono <- dbGetQuery(
  con,
  "SELECT
      h.Date,
      c.Time,
      t1.Other_Names AS Home_Team_Name,
      t2.Other_Names AS Away_Team_Name,
      h.H_percent,
      h.D_percent,
      h.A_percent,
      h.score_pred,
      h.score_pred_percent,
      c.score_home,
      c.score_away,
      c.result
   FROM Prono_history AS h
   JOIN Table_teams AS t1 ON h.H_team = t1.Id
   JOIN Table_teams AS t2 ON h.A_team = t2.Id
   JOIN Calendrier AS c ON c.Home_id = h.H_team
                        AND c.Away_id = h.A_team;"
)

dbDisconnect(con)

# Define server logic required to draw a histogram
function(input, output, session) {

  output$history_table <- renderDataTable({
    datatable(
      df_prono %>% 
        filter(!is.na(result)) %>% 
        arrange(desc(Date)),
      options = list(
        pageLength = 15,
        dom = 'frtip',
        autoWidth = TRUE
      ),
      rownames = FALSE,
      class = "stripe hover"
    )
  })
  
  output$next_game_table <- renderDataTable({
    
    # Filtrer et préparer les données
    df_prono %>%
      filter(is.na(result), ymd(Date) - today() == 0) %>%
      arrange(Time) %>%
      select(-c(score_home, score_away, result)) %>% 
      datatable(
        options = list(
          pageLength = 10,
          dom = '',
          autoWidth = TRUE
        ),
        rownames = FALSE,
        class = "stripe hover"
      ) 
  })
  
}
