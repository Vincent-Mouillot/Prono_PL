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
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
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
    
    df_prono <- df_prono %>% 
      filter(is.na(result),
             ymd(Date) - today() >= 0) %>%
      arrange(Time)
    
    df_prono$Matchup <- paste(df_prono$Home_Team_Name, "vs", df_prono$Away_Team_Name)
    
    df_prono$Matchup <- factor(df_prono$Matchup, levels = df_prono$Matchup)
    
    df_long <- df_prono %>% 
      pivot_longer(cols = c(H_percent, D_percent, A_percent), 
                   names_to = "Outcome", 
                   values_to = "Percentage") %>%
      mutate(
        Outcome = factor(Outcome, levels = c("H_percent", "D_percent", "A_percent"))
      )
    
    matchups <- unique(df_long$Matchup)
    n_matches <- length(matchups)
    
    plots <- lapply(matchups, function(match) {
      plot_ly(
        data = df_long %>% filter(Matchup == match),
        height = max(100 * n_matches, 200)
      ) %>% 
      add_trace(
        x = ~Percentage,
        y = ~"",
        color = ~Outcome,
        colors = c("H_percent" = df_long %>%
                     filter(Matchup == match) %>%
                     pull(Home_color) %>%
                     unique(),
                   "D_percent" = "gray",
                   "A_percent" = df_long %>%
                     filter(Matchup == match) %>%
                     pull(Away_color) %>%
                     unique()),
        type = 'bar',
        orientation = 'h',
        width = .1
      ) %>%
        layout(
          xaxis = list(
            title = "",
            showgrid = FALSE,
            zeroline = FALSE,
            showticklabels = FALSE
          ),
          yaxis = list(
            title = "",
            showgrid = FALSE,
            zeroline = FALSE,
            showticklabels = FALSE
          ),
          barmode = 'stack',
          showlegend = FALSE,
          annotations = list(
            list(
              x = 0,
              y = 0.7,
              text = df_long %>%
                filter(Matchup == match) %>%
                pull(Home_Team_Name) %>%
                unique(),
              xref = "paper",
              yref = "paper",
              xanchor = "left",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = "black"
              )
            ),
            list(
              x = 0.95,
              y = 0.7,
              text = df_long %>%
                filter(Matchup == match) %>%
                pull(Away_Team_Name) %>%
                unique(),
              xref = "paper",
              yref = "paper",
              xanchor = "right",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = "black"
              )
            ),
            list(
              x = 0.5,
              y = 1,
              text = df_long %>%
                filter(Matchup == match) %>%
                pull(Date) %>%
                unique(),
              xref = "paper",
              yref = "paper",
              xanchor = "center",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = "black"
              )
            ),
            list(
              x = 0.5,
              y = 0.7,
              text = df_long %>%
                filter(Matchup == match) %>%
                pull(Time) %>%
                unique(),
              xref = "paper",
              yref = "paper",
              xanchor = "center",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = "black"
              )
            ),
            list(
              x = (df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "H_percent") %>% 
                pull(Percentage) / 200) - 0.025,
              y = 0.3,
              text = df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "H_percent") %>% 
                pull(Percentage),
              xref = "paper",
              yref = "paper",
              xanchor = "center",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = df_long %>%
                  filter(Matchup == match) %>%
                  pull(Home_color) %>%
                  unique()
              )
            ),
            list(
              x = (df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "H_percent") %>% 
                pull(Percentage) / 100 + 
                df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "D_percent") %>% 
                pull(Percentage) / 200) - 0.025,
              y = 0.3,
              text = df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "D_percent") %>% 
                pull(Percentage),
              xref = "paper",
              yref = "paper",
              xanchor = "center",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = "gray"
              )
            ),
            list(
              x = (1 - df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "A_percent") %>% 
                pull(Percentage) / 200) - 0.025,
              y = 0.3,
              text = df_long %>% 
                filter(Matchup == match) %>%
                filter(Outcome == "A_percent") %>% 
                pull(Percentage),
              xref = "paper",
              yref = "paper",
              xanchor = "center",
              yanchor = "middle",
              showarrow = FALSE,
              font = list(
                size = 16,
                color = df_long %>%
                  filter(Matchup == match) %>%
                  pull(Away_color) %>%
                  unique()
              )
            )
          )
        )
    })
    
    fig <- subplot(plots, nrows = n_matches, shareX = TRUE, titleX = TRUE, titleY = FALSE)
    
    fig
  })
  
  
  
}
