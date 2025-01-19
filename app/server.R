library(shiny)
library(tidyverse)
library(DT)
library(DBI)
library(RSQLite)
library(rprojroot)
library(ggplot2)
library(plotly)

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
  
  output$next_game_graph <- renderPlotly({
    
    # Filtrage et tri des données par Time
    df_prono <- df_prono %>% 
      filter(is.na(result),
             ymd(Date) - today() == 0) %>%
      arrange(Time)
    
    # Création d'une colonne "Matchup" pour inclure les deux équipes
    df_prono$Matchup <- paste(df_prono$Home_Team_Name, "vs", df_prono$Away_Team_Name)
    
    # Ordonnancement explicite de la colonne Matchup selon Time
    df_prono$Matchup <- factor(df_prono$Matchup, levels = df_prono$Matchup)
    
    # Transformation des données au format long
    df_long <- df_prono %>% 
      pivot_longer(cols = c(H_percent, D_percent, A_percent), 
                   names_to = "Outcome", 
                   values_to = "Percentage")
    
    # Création du graphique interactif avec Plotly
    plot_ly(
      data = df_long,
      x = ~Percentage,
      y = ~Matchup,
      color = ~Outcome,
      colors = c("H_percent" = "blue", "D_percent" = "gray", "A_percent" = "red"),
      type = 'bar',
      orientation = 'h'
    ) %>%
      layout(
        barmode = 'stack',
        title = "Pourcentages cumulés par match",
        xaxis = list(title = "Pourcentage"),
        yaxis = list(title = ""),
        legend = list(title = list(text = "Résultat"), orientation = "h", x = 0.3, y = -0.1),
        margin = list(l = 100, r = 20, t = 40, b = 40)
      )
  })
  
  
  
}
