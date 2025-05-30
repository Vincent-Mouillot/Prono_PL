library(dplyr)
library(stringr)
library(rvest)
library(purrr)
library(tidyr)
library(progress)
library(DBI)
library(RSQLite)
library(glue)

url <- "https://fbref.com/en/comps/9/calendrier/Scores-et-tableaux-Premier-League"
page_calend <- read_html(url)
match_report_links <- page_calend %>% html_elements(xpath = "//a[contains(., 'Match Report')]")

# Extract the href attribute (link) of each matched link
report_links <- match_report_links %>% html_attr("href")

home_team_id <- page_calend %>%
  html_elements("table") %>%
  html_elements("tr") %>%
  html_elements("td:nth-child(5) a") %>%
  html_attr("href") %>%
  str_sub(12, 19)

away_team_id <- page_calend %>%
  html_elements("table") %>%
  html_elements("tr") %>%
  html_elements("td:nth-child(9) a") %>%
  html_attr("href") %>%
  str_sub(12, 19)

calendrier <- page_calend %>% html_element("table") %>% html_table() %>%
  select(Wk, Day, Date, Time, Home, Score, Away, Attendance, Referee) %>%
  filter(!is.na(Wk)) %>%
  mutate(Score = gsub("\u2013", "-", Score)) %>%
  separate(
    Score,
    into = c("score_home", "score_away"),
    sep = "-",
    convert = TRUE
  ) %>%
  mutate(
    result = case_when(
      score_home > score_away ~ "H",
      score_home < score_away ~ "A",
      score_home == score_away ~ "D"
    )
  )

# Get the row number where the game is not played
lignes_na <- which(is.na(calendrier$result))

# Add links NA for these games
for (ligne in rev(lignes_na)) {
  report_links <- append(report_links, NA, after = ligne - 1)
}

calendrier <- calendrier %>% 
  mutate(
    link = paste0(
      "https://fbref.com/",
      if_else(
        row_number() <= length(report_links),
        report_links[row_number()],
        NA_character_
      )
    ),
    id = str_extract(link, "[[:alnum:]]{8}"),
    Home_id = home_team_id,
    Away_id = away_team_id
  )

# Define the function to perform the database operations
perform_db_operations <- function() {
  # Define the name of the SQLite database file
  sqlite_file <- file.path(root, "Prono_PL", "my_database.db")
  
  # Check if the database file exists
  if (!file.exists(sqlite_file)) {
    stop("Error: Database file does not exist at the specified path.")
  }
  
  # Attempt to connect to the SQLite database
  con <- tryCatch({
    dbConnect(RSQLite::SQLite(), dbname = sqlite_file)
  }, error = function(e) {
    message("Error: Could not connect to the SQLite database.")
    message("Details: ", e$message)
    return(NULL)
  })
  
  # Stop execution if connection failed
  if (is.null(con))
    return(NULL)
  
  # Drop the table if it already exists
  tryCatch({
    dbExecute(con, "DROP TABLE IF EXISTS Calendrier;")
  }, error = function(e) {
    message("Error: Could not drop the table 'Calendrier'.")
    message("Details: ", e$message)
    dbDisconnect(con)
    return(NULL)
  })
  
  # Check if the 'calendrier' DataFrame exists
  if (!exists("calendrier")) {
    message("Error: 'calendrier' DataFrame does not exist.")
    dbDisconnect(con)
    return(NULL)
  }
  
  # Write the DataFrame to the SQLite database as a table
  tryCatch({
    dbWriteTable(con,
                 "Calendrier",
                 calendrier,
                 overwrite = TRUE,
                 row.names = FALSE)
  }, error = function(e) {
    message("Error: Could not write the DataFrame to the database.")
    message("Details: ", e$message)
    dbDisconnect(con)
    return(NULL)
  })
  
  # Close the database connection
  dbDisconnect(con)
  message("Database operations completed successfully.")
}

# Call the function
perform_db_operations()