library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(data.table)

root <- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

sqlite_file <- file.path(root, "Prono_PL", "my_database.db")

con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

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

df_opta <- dbGetQuery(
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

dbDisconnect(con)

one_hot <- as.data.table(model.matrix(~ result - 1, data = df_compl))
setnames(one_hot, old = colnames(one_hot), new = gsub("result", "result_", colnames(one_hot)))
df_compl <- cbind(df_compl, one_hot) %>% 
  select(-result)

one_hot_op <- as.data.table(model.matrix(~ result - 1, data = df_opta))
setnames(one_hot_op, old = colnames(one_hot_op), new = gsub("result", "result_", colnames(one_hot_op)))
df_opta <- cbind(df_opta, one_hot_op) %>% 
  select(-result)

brier_score <- function(df, mean=FALSE){
  df <- df %>% 
    mutate(H_percent = H_percent/100,
           D_percent = D_percent/100,
           A_percent = A_percent/100,
           Brier_score = (result_H - H_percent)^2 + 
             (result_D - D_percent)^2 + 
             (result_A - A_percent)^2)
  
  if(mean == TRUE){
    df <- mean(df$Brier_score)
  }
  
  return(df)
}

brier_score(df_compl, mean=TRUE)
brier_score(df_opta, mean=TRUE)
