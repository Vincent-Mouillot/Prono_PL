library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(caret)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "preprocessing.R"))

# Fixer la graine pour la reproductibilité
set.seed(42)

encoded_training_df <- encoded_df %>% 
  filter(!is.na(Score)) %>% 
  select(-c(Wk, Date, Day, Time, Team_id, Team, Opponent_id, Opponent, Score_opp))

# Créer un modèle de régression linéaire pour prédire "Score" sur l'ensemble complet
#model <- lm(Score ~ ., data = encoded_training_df)
model <- lm(Score ~ .^2, data = encoded_training_df)

# Both directions (forward and backward stepwise)
both_model <- step(model, direction = "both")

# Résumé du modèle résultant
summary(both_model)

# Supposons que 'future_matches_df' est le dataframe avec les futurs matchs
# Assurez-vous que 'future_matches_df' contient les mêmes colonnes que 'encoded_df', à l'exception de 'Score'
# Exemple : 
future_matches_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 14) %>% 
  select(-c(Wk, Date, Team_id, Team, Opponent_id, Opponent, Score_opp)) %>% 
  head(40) 
  

# Prédire sur les futurs matchs
future_predictions <- predict(model, newdata = future_matches_df)

future_predictions <- ifelse(future_predictions < 0, 0.1, future_predictions)

# Afficher les prédictions
predictions_df <- df_long %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 14) %>% 
  head(40) %>%
  mutate(Score = future_predictions)
