library(dplyr)
library(rvest)
library(DBI)
library(RSQLite)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

df_team <- dbGetQuery(con, 
                      "SELECT * FROM Table_teams 
                      WHERE Comp = 'Premier League';")

dbDisconnect(con)

url <- "https://www.compare-bet.fr/cotes/premier-league.html"
page_cote <- read_html(url)

match <- page_cote %>%
  html_elements("h2.nom-match") %>%
  html_text(trim = TRUE)

test <- page_cote %>% 
  html_elements("div.bloc_match")

all_dfs <- list()

for (i in seq_along(test)) {
  site_names <- test[i] %>%
    html_elements("td a") %>%
    html_children() %>%
    html_attr("alt")
  
  odds <- test[i] %>%
    html_elements("td.cote") %>%
    html_text() %>% 
    as.numeric()
  
  if (length(odds) %% 3 != 0) {
    warning(paste("Odds for element", i, "are not a multiple of 3. Skipped."))
    next
  }
  
  df <- matrix(odds, ncol = 3, byrow = TRUE) %>%
    as.data.frame()
  colnames(df) <- c("H", "D", "A")
  
  if (length(site_names) != nrow(df)) {
    warning(paste("Number of sites and rows differ for element", i, ". Skipped."))
    next
  }
  
  match_parts <- str_split(match[i], " - ", simplify = TRUE)
  home_team <- match_parts[1]
  away_team <- match_parts[2]
  
  df <- df %>%
    mutate(
      Home = home_team,
      Away = away_team,
      Site = site_names
    ) %>%
    select(Home, Away, Site, H, D, A)
  
  all_dfs[[i]] <- df
}

df_book <- bind_rows(all_dfs) %>% 
  left_join(
    df_team %>% 
      select(Id, Opta_Name),
    by = c("Home" = "Opta_Name")
  ) %>% 
  left_join(
    df_team %>% 
      select(Id, Other_Names) %>%
      mutate(Other_Names = if_else(Other_Names == "Wolverhampton Wanderers",
                                   "Wolverhampton", 
                                   Other_Names)),
    by = c("Home" = "Other_Names")
  ) %>% 
  mutate(H_team = coalesce(Id.x, Id.y)) %>%
  select(-Id.x, -Id.y) %>% 
  left_join(
    df_team %>% 
      select(Id, Opta_Name),
    by = c("Away" = "Opta_Name")
  ) %>% 
  left_join(
    df_team %>% 
      select(Id, Other_Names) %>%
      mutate(Other_Names = if_else(Other_Names == "Wolverhampton Wanderers",
                                   "Wolverhampton", 
                                   Other_Names)),
    by = c("Away" = "Other_Names")
  ) %>% 
  mutate(A_team = coalesce(Id.x, Id.y)) %>%
  select(H_team, A_team, Site, H, D, A) %>% 
  mutate(H_prob = (1 / H),
         D_prob = (1 / D),
         A_prob = (1 / A),
         H_percent = round((H_prob / (H_prob + D_prob + A_prob)) * 100, 0),
         D_percent = round((D_prob / (H_prob + D_prob + A_prob)) * 100, 0),
         A_percent = round((A_prob / (H_prob + D_prob + A_prob)) * 100, 0)) %>% 
  select(-c(H_prob, D_prob, A_prob))

# Connect to the SQLite database
con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

# Create the Book_history table if it doesn't exist
dbExecute(con, "
  CREATE TABLE IF NOT EXISTS Book_history (
    H_team TEXT,
    A_team TEXT,
    Site TEXT,
    H REAL,
    D REAL,
    A REAL,
    H_percent REAL,
    D_percent REAL,
    A_percent REAL,
    PRIMARY KEY (H_team, A_team, Site)
  );
")

# Function to insert or update the data in the Book_history table
insert_or_update_book_history <- function(df_book, con) {
  
  for (i in 1:nrow(df_book)) {
    # Extract the values of a dataframe row
    H_team <- df_book$H_team[i]
    A_team <- df_book$A_team[i]
    site <- df_book$Site[i]
    h <- df_book$H[i]
    d <- df_book$D[i]
    a <- df_book$A[i]
    h_percent <- df_book$H_percent[i]
    d_percent <- df_book$D_percent[i]
    a_percent <- df_book$A_percent[i]
    
    # Check if the combination already exists using a parameterized query
    query <- dbGetQuery(con, "
      SELECT COUNT(*) AS count FROM Book_history
      WHERE H_team = ? AND A_team = ? AND Site = ?", 
                        params = list(H_team, A_team, site)
    )
    
    if (query$count == 0) {
      # If the combination doesn't exist, insert the data (parameterized query)
      dbExecute(con, "
        INSERT INTO Book_history (H_team, A_team, Site, H, D, A, H_percent, D_percent, A_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                params = list(H_team, A_team, site, h, d, a, h_percent, d_percent, a_percent)
      )
    } else {
      # If the combination exists, update the other columns (parameterized query)
      dbExecute(con, "
        UPDATE Book_history
        SET H = ?, D = ?, A = ?, H_percent = ?, D_percent = ?, A_percent = ?
        WHERE H_team = ? AND A_team = ? AND Site = ?", 
                params = list(h, d, a, h_percent, d_percent, a_percent, H_team, A_team, site)
      )
    }
  }
}

# Call the function to insert or update the data
insert_or_update_book_history(df_book, con)

# Disconnect from the database
dbDisconnect(con)
