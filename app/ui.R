library(shiny)
library(shinydashboard)
library(plotly)

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
              h1("Prono for the next 3 days"),
              plotlyOutput("next_game_graph")),
      tabItem(
        tabName = "perf_model", 
        h2("Brier Score!"),
        tabBox(
          title = "Performance Metrics",
          id = "tabset1",
          width = 12,
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
          ),
          tabPanel(
            title = "Autre Métrique",
            h3("Autre Analyse"),
            textOutput("other_metric_text")
          )
        )
      ),
      tabItem(tabName = "history", h2("Table of last prono"),
              dataTableOutput("history_table"))
    )
  )
)
