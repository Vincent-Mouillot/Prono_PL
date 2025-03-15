library(shiny)
library(tidyverse)
library(DT)
library(DBI)
library(RSQLite)
library(rprojroot)
library(ggplot2)
library(plotly)
library(gt)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "compute_brier_score.R"))

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

# dbDisconnect(con)

function(input, output, session) {
  
  output$next_game_graph <- renderPlotly({
    
    df_prono <- df_prono %>% 
      filter(is.na(result),
             ymd(Date) - today() >= 0) %>%
      arrange(Date, Time)
    
    if (nrow(df_prono) == 0) {
      return(NULL)
    }
    
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
  
  output$comp_next_game <- render_gt({
    df_model <- dbGetQuery(
      con,
      "SELECT
      h.Date,
      c.Time,
      t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
      'Model' AS Site,
      h.H_percent,
      h.D_percent,
      h.A_percent
   FROM Prono_history AS h
   JOIN Table_teams AS t1 ON h.H_team = t1.Id
   JOIN Table_teams AS t2 ON h.A_team = t2.Id
   JOIN Calendrier AS c ON c.Home_id = h.H_team
                        AND c.Away_id = h.A_team
   WHERE c.result IS NULL;"
    )
    
    if (nrow(df_model) == 0) {
      return(NULL)
    }
    
    df_opta <- dbGetQuery(
      con,
      "SELECT
      h.Date,
      c.Time,
      t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
      'Opta' AS Site,
      o.H_percent,
      o.D_percent,
      o.A_percent
   FROM Prono_history AS h
   JOIN Table_teams AS t1 ON h.H_team = t1.Id
   JOIN Table_teams AS t2 ON h.A_team = t2.Id
   JOIN Calendrier AS c ON c.Home_id = h.H_team
                        AND c.Away_id = h.A_team
   JOIN Opta AS o ON o.H_team = h.H_team
                        AND o.A_team = h.A_team
   WHERE c.result IS NULL;"
    )
    
    df_compl <- dbGetQuery(
      con,
      "SELECT r.Date,
  r.Time,
  t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
          p.Site,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Book_history AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      JOIN Table_teams AS t1 ON p.H_team = t1.Id
   JOIN Table_teams AS t2 ON p.A_team = t2.Id
      WHERE r.result IS NULL
  AND Site IN ('Winamax', 'Parionssport');"
    )
    
    # Supposons que df_compl est votre data frame initial
    df <- df_model %>% 
      bind_rows(df_opta) %>% 
      bind_rows(df_compl)
    
    # Créer les colonnes de barres
    df$H_Bar <- sprintf(
      '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: %s; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
      df$Home_color,
      df$H_percent,
      df$H_percent
    )
    
    df$D_Bar <- sprintf(
      '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: #D3D3D3; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
      df$D_percent,
      df$D_percent
    )
    
    df$A_Bar <- sprintf(
      '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: %s; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
      df$Away_color,
      df$A_percent,
      df$A_percent
    )
    
    # Créer une colonne unique pour le regroupement
    df$Match <- paste(df$Date, " ", df$Time, " - ", df$Home_Team_Name, "vs", df$Away_Team_Name)
    
    # Créer la table gt avec des groupes de lignes
    gt_table <- gt(df %>% 
                     select(Match, Site, H_Bar, D_Bar, A_Bar),
                   groupname_col = "Match") %>%
      tab_header(
        title = "Match Results with Bars"
      ) %>%
      cols_label(
        H_Bar = md("**Home Bar**"),
        D_Bar = md("**Draw Bar**"),
        A_Bar = md("**Away Bar**")
      ) %>%
      fmt_markdown(columns = c(H_Bar, D_Bar, A_Bar)) %>%
      cols_width(
        # Définir la largeur des colonnes
        c(Match) ~ "100%",   # Largeur de 100% pour la colonne "Match"
        c(Site) ~ "10%",     # Largeur de 10% pour la colonne "Site"
        c(H_Bar, D_Bar, A_Bar) ~ "30%"  # Largeur de 30% pour les barres
      ) %>%
      tab_style(
        style = list(
          cell_text(weight = "bold", align = "center")  # Mettre en gras et centrer le texte
        ),
        locations = cells_column_labels(columns = c(Match))  # Applique le style aux étiquettes de la colonne "Match"
      ) %>%
      tab_style(
        style = cell_text(align = "center"),  # Centrer le texte dans les cellules de la colonne "Match"
        locations = cells_body(columns = c(Match))  # Applique aux cellules de la colonne "Match"
      )
    
    # Afficher la table
    gt_table
  })
  
  output$side_predictions <- renderPlotly({
    df_long <- df_prono %>%
      select(H_percent, D_percent, A_percent) %>%
      pivot_longer(cols = everything(), names_to = "Category", values_to = "Value") %>%
      mutate(Category = factor(Category, levels = c("H_percent", "D_percent", "A_percent")))
    
    p <- ggplot(df_long, aes(x = Category, y = Value, fill = Category)) +
      geom_boxplot() +
      theme_minimal() +
      ylim(c(0, 100)) +
      theme(legend.position = "none") +
      labs(x = "", y = "", title = "Boxplot of side predictions")
    
    ggplotly(p)
  })
  
  output$nb_good_pr <- renderValueBox({
    df <- df_prono %>% 
      filter(!is.na(result)) %>% 
      mutate(Score = paste0(score_home, "-", score_away),
                      Result_pred = names(df_prono %>% 
                                            select(H_percent, A_percent, D_percent))[max.col(select(., H_percent, A_percent, D_percent))] %>% 
                        str_remove("_percent")) %>% 
      select(result, Result_pred) %>% 
      mutate(Good_result = if_else(
        result == Result_pred,
        TRUE,
        FALSE
        )
      )
    nb <- df$Good_result %>% 
      sum()
    nb_prono <- df$Good_result %>% 
      length()
    prop <- (nb / nb_prono) %>% 
      round(2) * 100
    valueBox(
      value = paste0(nb, "/", nb_prono, " or ", prop, "%"),
      subtitle = "Number of good outcome predictions",
      icon = icon("chart-line"),
      color = "blue"
    )
  })
  
  output$nb_good_result <- renderValueBox({
    df <- df_prono %>% 
      filter(!is.na(result)) %>% 
      mutate(Score = paste0(score_home, "-", score_away),
             Result_pred = names(df_prono %>% 
                                   select(H_percent, A_percent, D_percent))[max.col(select(., H_percent, A_percent, D_percent))] %>% 
               str_remove("_percent")) %>% 
      select(Score, score_pred) %>% 
      mutate(
        Good_score = if_else(
          Score == score_pred,
          TRUE,
          FALSE
        )
      )
    nb <- df$Good_score %>% 
      sum()
    nb_prono <- df$Score %>% 
                   length()
    prop <- (nb / nb_prono) %>% 
      round(2) * 100
    valueBox(
      value = paste0(nb, "/", nb_prono, " or ", prop, "%"),
      subtitle = "Number of good result predictions",
      icon = icon("chart-line"),
      color = "blue"
    )
  })
  
  output$model_brier_box <- renderValueBox({
    df_compl <- dbGetQuery(
      con,
      "SELECT p.H_team,
          p.A_team,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Prono_history AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      WHERE r.result IS NOT NULL;"
    )
    brier_value <- brier_score(df_compl, mean=TRUE)
    valueBox(
      value = brier_value,
      subtitle = "Brier score of the model",
      icon = icon("chart-line"),
      color = if_else(brier_value < 2/3, "green", "red")
    )
  })
  
  output$opta_brier_box <- renderValueBox({
    df_compl <- dbGetQuery(
      con,
      "SELECT p.H_team,
          p.A_team,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Opta AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      WHERE r.result IS NOT NULL;"
    )
    brier_value <- brier_score(df_compl, mean=TRUE)
    valueBox(
      value = brier_value,
      subtitle = "Brier score of Opta",
      icon = icon("chart-line"),
      color = if_else(brier_value < 2/3, "green", "red")
    )
  })
  
  output$winamax_brier_box <- renderValueBox({
    df_compl <- dbGetQuery(
      con,
      "SELECT p.H_team,
          p.A_team,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Book_history AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      WHERE r.result IS NOT NULL
        AND Site='Winamax';"
    )
    brier_value <- brier_score(df_compl, mean=TRUE)
    valueBox(
      value = brier_value,
      subtitle = "Brier score of Winamax",
      icon = icon("chart-line"),
      color = if_else(brier_value < 2/3, "green", "red")
    )
  })
  
  output$parionssport_brier_box <- renderValueBox({
    df_compl <- dbGetQuery(
      con,
      "SELECT p.H_team,
          p.A_team,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Book_history AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      WHERE r.result IS NOT NULL
        AND Site='Parionssport';"
    )
    brier_value <- brier_score(df_compl, mean=TRUE)
    valueBox(
      value = brier_value,
      subtitle = "Brier score of Parions Sport",
      icon = icon("chart-line"),
      color = if_else(brier_value < 2/3, "green", "red")
    )
  })

  output$history_table <- renderDataTable({
    datatable(
      df_prono %>% 
        filter(!is.na(result)) %>% 
        arrange(desc(Date)) %>% 
        select(-c(Home_color, Away_color)),
      filter = list(position = 'top', clear = FALSE),
      options = list(
        pageLength = 15,
        dom = 'frtip',
        autoWidth = TRUE,
        scrollX = TRUE
      ),
      rownames = FALSE,
      class = "stripe hover"
    )
  })
  
  session$onSessionEnded(function() {
    dbDisconnect(con)
    cat("Connexion à la base de données fermée.\n")
  })
}
