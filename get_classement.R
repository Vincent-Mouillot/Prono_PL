library(dplyr)
library(stringr)
library(rvest)
library(purrr)
library(tidyr)
library(progress)
library(DBI)
library(RSQLite)
library(glue)
library(taskscheduleR)

df <- data.frame(
  Squad = c(
    "Manchester City", "Arsenal", "Liverpool", "Aston Villa", "Tottenham", 
    "Chelsea", "Newcastle Utd", "Manchester Utd", "West Ham", "Crystal Palace", 
    "Brighton", "Bournemouth", "Fulham", "Wolves", "Everton", 
    "Brentford", "Nott'ham Forest", "Leicester City", "Ipswich Town", "Southampton"
  ),
  J0 = 1:20
) %>% arrange(Squad)



url <- "https://fbref.com/en/comps/9/Premier-League-Stats"
page_classement <- read_html(url)

team_id <- page_classement %>%
  html_node("#results2024-202591_overall") %>%  # Select the table by its ID
  html_nodes('td[data-stat="team"] a') %>%  # Select <a> tags within <td> elements that have the attribute data-stat="team"
  html_attr("href") %>%
  str_sub(12, 19)

class <- page_classement %>% 
  html_element("#results2024-202591_overall") %>% 
  html_table() %>% 
  select(
    Rk,
    MP
  ) %>% 
  mutate(Id = team_id)

# Assuming your DataFrame is named "df"
most_common_value <- class %>%
  count(MP) %>%
  arrange(desc(n)) %>%
  slice(1) %>%
  pull(MP)

matchday <- paste0("J", most_common_value)

class <- class %>%
  select(Id, Rk) %>% 
  rename(!!matchday := Rk)

# Define the name of the SQLite database file
sqlite_file <- "C:/Users/vmoui/OneDrive/Bureau/Prono_sport/my_database.db"

# Function to perform database operations
perform_db_operations <- function() {
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
  dbWriteTable(con, "Classement", table_class, overwrite = TRUE, row.names = FALSE)
  
  # Close the database connection
  dbDisconnect(con)
  
  message("Database operations completed successfully.")
}

# Call the function
perform_db_operations()