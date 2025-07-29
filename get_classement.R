library(dplyr)
library(stringr)
library(rvest)
library(purrr)
library(tidyr)
library(progress)
library(DBI)
library(RSQLite)
library(glue)

df <- data.frame(
  Squad = c(
    "Liverpool",
    "Arsenal",
    "Manchester City",
    "Chelsea",
    "Newcastle Utd",
    "Aston Villa",
    "Nott'ham Forest",
    "Brighton",
    "Bournemouth",
    "Brentford",
    "Fulham",
    "Crystal Palace",
    "Everton",
    "West Ham",
    "Manchester Utd",
    "Wolves",
    "Tottenham",
    "Leeds United",
    "Burnley",
    "Sunderland"
  ),
  J0 = 1:20
) %>% arrange(Squad)

# Define the name of the SQLite database file
sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

url <- "https://fbref.com/en/comps/9/2025-2026/2025-2026-Premier-League-Stats"
page_classement <- read_html(url)

team_id <- page_classement %>%
  html_element("#results2025-202691_overall") %>%
  html_elements('td[data-stat="team"] a') %>%
  html_attr("href") %>%
  str_sub(12, 19)

class <- page_classement %>%
  html_element("#results2025-202691_overall") %>%
  html_table() %>%
  select(Rk, MP) %>%
  mutate(Id = team_id)

# Assuming your DataFrame is named "df"
most_common_value <- class %>%
  count(MP) %>%
  arrange(desc(n)) %>%
  slice(1) %>%
  pull(MP)


matchday <- paste0("J", most_common_value)

if (most_common_value == 0) {
  class <- class %>% 
    select(Id) %>%
    mutate(Rk = df$J0) %>% 
    rename(!!matchday := Rk)
  
  con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)
  dbWriteTable(con,
               "Classement",
               class,
               overwrite = TRUE,
               row.names = FALSE)
} else{
  class <- class %>%
    select(Id, Rk) %>%
    rename(!!matchday := Rk)
}


# Function to perform database operations
perform_db_operations <- function() {

  if (most_common_value == 0) {
    return(message("Operation done manually"))
  }
  
  # Attempt to connect to the SQLite database
  con <- try(dbConnect(RSQLite::SQLite(), dbname = sqlite_file), silent = TRUE)
  
  # Check if the connection was successful
  if (inherits(con, "try-error")) {
    message("Error: Could not connect to the SQLite database.")
    return(NULL)
  }
  
  # Attempt to retrieve the 'Classement' table
  table_class <- try(dbGetQuery(con, "SELECT * FROM Classement;"), silent = TRUE)
  
  # Check if the table was successfully retrieved
  if (inherits(table_class, "try-error")) {
    message("Error: Could not retrieve the 'Classement' table.")
    dbDisconnect(con)
    return(NULL)
  }
  
  # Attempt to select all columns except 'matchday'
  test_column <- try({
    table_class %>%
      select(-all_of(matchday))
  }, silent = TRUE)
  
  # Check if there was an error in column selection
  if (inherits(test_column, "try-error")) {
    message("Error: 'matchday' column does not exist. New 'matchday' added.")
  } else {
    table_class <- test_column
  }
  
  
  # Example: Assuming 'class' is a predefined DataFrame that needs to be joined
  if (exists("class")) {
    table_class <- table_class %>%
      left_join(class, by = "Id")
  } else {
    message("Error: 'class' DataFrame does not exist. Skipping join operation.")
  }
  
  # Drop the table if it already exists and write the new data
  dbExecute(con, "DROP TABLE IF EXISTS Classement;")
  dbWriteTable(con,
               "Classement",
               table_class,
               overwrite = TRUE,
               row.names = FALSE)
  
  # Close the database connection
  dbDisconnect(con)
  
  message("Database operations completed successfully.")
}

# Call the function
perform_db_operations()