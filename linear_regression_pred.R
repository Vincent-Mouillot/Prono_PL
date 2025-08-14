library(DBI)
library(RSQLite)
library(tidyverse)
library(rprojroot)
library(caret)
library(quantreg)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "preprocessing.R"))

# Fixer la graine pour la reproductibilité
set.seed(42)

encoded_training_df <- encoded_df %>% 
  filter(!is.na(Score)) %>% 
  select(-c(Wk, Date, Day, Time, Team_id, Team, Opponent_id, Opponent, Score_opp))

# Linear model
model_lin <- lm(Score ~ ., data = encoded_training_df)
step_model_lin <- MASS::stepAIC(model_lin, direction = "both")
summary(step_model_lin)
final_model_lin <- step_model_lin

# Quantile regression
nzv <- nearZeroVar(encoded_training_df)
encoded_training_df <- encoded_training_df[, -nzv]
model_rq <- rq(Score ~ ., data = encoded_training_df, tau = 0.55)
step_model_rq <- MASS::stepAIC(model_rq, direction = "both")
summary(step_model_rq)
final_model_rq <- step_model_rq

# Poisson model
model_poisson <- glm(Score ~ ., data = encoded_training_df, family = poisson(link = "log"))
step_model_pois <- MASS::stepAIC(model_poisson, direction = "both")
summary(step_model_pois)
final_model_pois <- step_model_pois

# Quasi Poisson
final_model_quasi_pois <- glm(formula(step_model_pois), data = encoded_training_df, family = quasipoisson())
summary(final_model_quasi_pois)

# Supposons que 'future_matches_df' est le dataframe avec les futurs matchs
# Assurez-vous que 'future_matches_df' contient les mêmes colonnes que 'encoded_df', à l'exception de 'Score'
# Exemple : 
future_matches_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 3,
         ymd(Date) - today() >= 0) %>% 
  select(-c(Wk, Date, Team_id, Team, Opponent_id, Opponent, Score_opp))
  
# Mettre toutes les predictions dans un df pour tous les modèles
prediction_df <- data.frame(Score_lin = predict(final_model_lin, newdata = future_matches_df),
                            Score_rq = predict(final_model_rq, newdata = future_matches_df),
                            Score_pois = predict(final_model_pois, newdata = future_matches_df),
                            Score_quasi_pois = predict(final_model_quasi_pois, newdata = future_matches_df))

# Prédire sur les futurs matchsS
future_predictions <- predict(final_model_rq, newdata = future_matches_df)

future_predictions <- ifelse(future_predictions < 0, 0.1, future_predictions)

# Afficher les prédictions
predictions_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 3,
         ymd(Date) - today() >= 0) %>% 
  mutate(Score = future_predictions)