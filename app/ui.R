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
              plotlyOutput("next_game_graph")),
      tabItem(tabName = "perf_model", h2("Brier Score!")),
      tabItem(tabName = "history", h2("Table of last prono"),
              dataTableOutput("history_table"))
    )
  )
)
