get_calendrier <- function(url = "https://fbref.com/en/comps/9/2025-2026/schedule/2025-2026-Premier-League-Scores-and-Fixtures",
                           db_filename = "my_database.db",
                           project_dirname = "Prono_PL") {
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
  
  root <- rprojroot::find_root(rprojroot::has_dir(project_dirname))
  # Define the name of the SQLite database file
  sqlite_file <- file.path(root, project_dirname, db_filename)
  
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
    dbWriteTable(con, "Calendrier", calendrier,                    overwrite = TRUE,
                   row.names = FALSE)
    }, error = function(e) {
      message("Error: Could not write the DataFrame to the database.")
      message("Details: ", e$message)
      dbDisconnect(con)
      return(NULL)
    })
    
    # Close the database connection
    dbDisconnect(con)
    
    return(message("Database operations completed successfully."))
}

clean_labels <- function(
    labels
) {
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

get_all_player_data <- function(
    url
) {
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
  na_to_na_list <- lapply(split(aria_labels, cumsum(is.na(aria_labels))), clean_labels) %>%
    Filter(function(x)
      length(x) > 2, .)
  
  # Extract and rename tables
  tables <- page %>%
    html_elements("tbody") %>%
    html_table() %>%
    map2(na_to_na_list, ~ {
      colnames(.x) <- .y
      .x
    })
  
  # Define keys for inner join
  keys <- c("Player",
            "Shirt_Number",
            "Nation",
            "Position",
            "Age",
            "Minutes")
  
  # Perform inner join on the first to the sixth table
  home_table <- reduce(tables[1:6],
                       inner_join,
                       by = keys,
                       suffix = c("", ".doublon"))
  
  home_table <- home_table %>%
    select(-ends_with(".doublon")) %>%
    mutate(team = squad_home_id)
  
  away_table <- reduce(tables[8:13],
                       inner_join,
                       by = keys,
                       suffix = c("", ".doublon"))
  
  away_table <- away_table %>%
    select(-ends_with(".doublon")) %>%
    mutate(team = squad_away_id)
  
  joined_table <- home_table %>%
    bind_rows(away_table) %>%
    mutate(game = game_id)
  
  Sys.sleep(sample(5:10, 1))
  
  return(joined_table)
}

get_player_stats <- function(
    db_filename = "my_database.db",
    project_dirname = "Prono_PL"
){
    root <- rprojroot::find_root(rprojroot::has_dir(project_dirname))
    # Define the name of the SQLite database file
    sqlite_file <- file.path(root, project_dirname, db_filename)
    
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
    progress_bar <- progress_bar$new(format = "  Scraping [:bar] :percent in :elapsed",
                                     total = length(input_data),
                                     width = 60)
    
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
      dbWriteTable(con,
                   "Stats_players",
                   results,
                   append = TRUE,
                  row.names = FALSE)
  }, error = function(e) {
    message("Error: Could not write results to 'Stats_players'.")
    message("Details: ", e$message)
  })
    
  # Close the database connection
  dbDisconnect(con)
    
  return(message("Database operations completed successfully."))

}