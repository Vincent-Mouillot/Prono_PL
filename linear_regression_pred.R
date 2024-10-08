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
  select(-Date)

# Créer un modèle de régression linéaire pour prédire "Score" sur l'ensemble complet
model <- lm(Score ~ . - 1, data = encoded_training_df)

# Supposons que 'future_matches_df' est le dataframe avec les futurs matchs
# Assurez-vous que 'future_matches_df' contient les mêmes colonnes que 'encoded_df', à l'exception de 'Score'
# Exemple : 
future_matches_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 3) %>% 
  head(20) 
  

# Prédire sur les futurs matchs
future_predictions <- predict(model, newdata = future_matches_df)

# Afficher les prédictions
predictions_df <- df_long %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 3) %>% 
  head(20) %>%
  mutate(Score = future_predictions)