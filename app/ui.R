library(shiny)
library(shinydashboard)
library(plotly)
library(gt)

dashboardPage(
  dashboardHeader(title = "Pronos PL"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Home", tabName = "home", icon = icon("home")),
      menuItem("Next games", tabName = "next_game", icon = icon("chart-line")),
      menuItem("Performance of the model", 
               tabName = "perf_model", icon = icon("chart-line")),
      menuItem("Prono history", tabName = "history", icon = icon("chart-line"))
    )
  ),
  dashboardBody(
    tags$head(
      tags$link(rel = "stylesheet", type = "text/css", href = "custom.css")
    ),
    tabItems(
      tabItem(tabName = "home", h2("Bienvenue dans l'application!")),
      tabItem(tabName = "next_game",
        tabBox(
          title = "Prono",
          id = "tabset_prono",
          width = 12,
          tabPanel(
            title = "Predictions of the model",
            plotlyOutput("next_game_graph")
          ),
          tabPanel(
            title = "Comparaison with bookmakers",
            gt_output("comp_next_game")
          )
        )
      ),
      tabItem(
        tabName = "perf_model", 
        tabBox(
          title = "Performance Metrics",
          id = "tabset1",
          width = 12,
          tabPanel(
            title = "Predictions",
            fluidRow(
              column(
                width = 4,
                valueBoxOutput("nb_good_pr", width = 12),
                valueBoxOutput("nb_good_result", width = 12)
              ),
              column(
                width = 8,
                plotlyOutput("side_predictions", width = "100%")
              )
            )
          ),
          tabPanel(
            title = "Brier Score",
            h3("Analyse du Brier Score"),
            fluidRow(
              valueBoxOutput("model_brier_box", width = 12)
            ),
            fluidRow(
              valueBoxOutput("opta_brier_box", width = 12)
            ),
            fluidRow(
              valueBoxOutput("winamax_brier_box", width = 12)
            ),
            fluidRow(
              valueBoxOutput("parionssport_brier_box", width = 12)
            )
          )
        )
      ),
      tabItem(tabName = "history", h2("Table of last prono"),
              dataTableOutput("history_table"))
    )
  )
)
