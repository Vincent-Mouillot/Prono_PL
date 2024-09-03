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

clean_labels <- function(labels) {
  # Remove NA values
  labels <- na.omit(labels)
  
  # Remove empty strings
  labels <- labels[labels != ""]
  
  # Replace "%" with "Perc"
  labels <- gsub("%", "Perc", labels)
  
  # Remove punctuation signs and replace spaces with underscores
  labels <- gsub("[[:punct:]]", "", labels)
  labels <- gsub(" ", "_", labels)
  
  return(labels)
}

get_all_player_data <- function(url) {
  page <- read_html(url)
  
  game_id <- url %>% 
    str_extract("[[:alnum:]]{8}")
  
  info <- page %>% 
    html_elements("strong a") %>%
    html_attr("href") 
  
  squad_home <- info[1] %>% 
    str_split_1("/")
  
  squad_home_id <- squad_home[4]
  
  squad_away <- info[2] %>% 
    str_split_1("/")
  
  squad_away_id <- squad_away[4]
  
  # Extract aria-label attributes for table headers
  aria_labels <- page %>%
    html_elements("th") %>%
    html_attr("aria-label")
  
  # Clean and filter the extracted labels
  na_to_na_list <- lapply(split(aria_labels, cumsum(is.na(aria_labels))),
                          clean_labels) %>%
    Filter(function(x) length(x) > 2, .)
  
  # Extract and rename tables
  tables <- page %>%
    html_elements("tbody") %>%
    html_table() %>%
    map2(na_to_na_list, ~ { colnames(.x) <- .y; .x })
  
  # Define keys for inner join
  keys <- c("Player", "Shirt_Number", "Nation", "Position", "Age", "Minutes")
  
  # Perform inner join on the first to the sixth table
  home_table <- reduce(tables[1:6], inner_join, by = keys, suffix = c("", ".doublon"))
  
  home_table <- home_table %>%
    select(-ends_with(".doublon")) %>% 
    mutate(team = squad_home_id)
  
  away_table <- reduce(tables[8:13], inner_join, by = keys, suffix = c("", ".doublon"))
  
  away_table <- away_table %>%
    select(-ends_with(".doublon"))%>% 
    mutate(team = squad_away_id)
  
  joined_table <- home_table %>% 
    bind_rows(away_table) %>% 
    mutate(game = game_id)
  
  Sys.sleep(sample(5:10, 1))  
  
  return(joined_table)
}

# Define the function to perform database operations
perform_db_operations <- function() {
  # Define the name of the SQLite database file
  sqlite_file <- "my_database.db"
  
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
  if (is.null(con)) return(NULL)
  
  # Retrieve the IDs to remove
  id_to_remove <- tryCatch({
    dbGetQuery(con, "SELECT DISTINCT game FROM Stats_players;")
  }, error = function(e) {
    message("Error: Could not retrieve data from 'Stats_players'.")
    message("Details: ", e$message)
    dbDisconnect(con)
    return(NULL)
  })
  
  # Retrieve the 'Calendrier' data
  calendrier <- tryCatch({
    dbGetQuery(con, "SELECT * FROM Calendrier;")
  }, error = function(e) {
    message("Error: Could not retrieve data from 'Calendrier'.")
    message("Details: ", e$message)
    dbDisconnect(con)
    return(NULL)
  })
  
  # Filter the data
  input_data <- calendrier %>%
    filter(!id %in% id_to_remove$game, link != "https://fbref.com/NA") %>%
    select(link) %>%
    pull()
  
  # Set up the progress bar
  progress_bar <- progress_bar$new(
    format = "  Scraping [:bar] :percent in :elapsed",
    total = length(input_data),
    width = 60
  )
  
  # Initialize the results data frame
  results <- data.frame()
  
  # Scrape data and update the progress bar
  for (i in input_data) {
    result <- tryCatch({
      get_all_player_data(i)
    }, error = function(e) {
      message("Error: Failed to scrape data from link ", i)
      message("Details: ", e$message)
      return(data.frame()) # Return an empty data frame on failure
    })
    
    results <- rbind(results, result)
    progress_bar$tick()
  }
  
  # Replace NA values with 0 in the results
  results <<- results %>%
    mutate(across(everything(), ~ replace_na(.x, 0)))
  
  # Append the results to the 'Stats_players' table
  tryCatch({
    dbWriteTable(con, "Stats_players", results, append = TRUE, row.names = FALSE)
  }, error = function(e) {
    message("Error: Could not write results to 'Stats_players'.")
    message("Details: ", e$message)
  })
  
  # Close the database connection
  dbDisconnect(con)
  message("Database operations completed successfully.")
}

# Call the function
perform_db_operations()