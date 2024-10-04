# Charger les bibliothèques nécessaires
library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(caret)

# Charger vos données et prétraiter (préprocessing)
source("preprocessing.R")

# Fixer la graine pour la reproductibilité
set.seed(42)

encoded_training_df <- encoded_df %>% 
  filter(!is.na(Score))

# Créer un modèle de régression linéaire pour prédire "Score" sur l'ensemble complet
model <- lm(Score ~ ., data = encoded_training_df)

# Résumé du modèle
summary(model)

# Supposons que 'future_matches_df' est le dataframe avec les futurs matchs
# Assurez-vous que 'future_matches_df' contient les mêmes colonnes que 'encoded_df', à l'exception de 'Score'
# Exemple : 
future_matches_df <- encoded_df %>% 
  filter(is.na(Score)) %>% 
  head(20)

# Prédire sur les futurs matchs
future_predictions <- predict(model, newdata = future_matches_df)

# Afficher les prédictions
predictions_df <- df_long %>% 
  filter(is.na(Score)) %>% 
  head(20) %>%
  mutate(Score = future_predictions)