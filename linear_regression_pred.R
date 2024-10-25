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

# model <- lm(Score ~ ., data = encoded_training_df)
# both_model <- step(model, direction = "both")
# summary(both_model)
# final_model <- both_model

model <- rq(Score ~ ., data = encoded_training_df, tau = 0.65)
both_model <- step(model, direction = "both")
summary(both_model)
final_model <- both_model

# poisson_model <- glm(Score ~ ., data = encoded_training_df, family = poisson())
# step_poisson_model <- MASS::stepAIC(poisson_model, direction = "both", trace = TRUE)
# final_quasi_poisson_model <- glm(formula(step_poisson_model), data = encoded_training_df, family = quasipoisson())
# summary(final_quasi_poisson_model)
# # Vérifier la surdispersion
# dispersion <- sum(residuals(final_quasi_poisson_model, type = "pearson")^2) / final_quasi_poisson_model$df.residual
# print(dispersion)
# final_model <- final_quasi_poisson_model

# Assumons que data_vector contient des comptages et une covariable (X)
# model_poisson <- glm(Score ~ ., data = encoded_training_df, family = poisson(link = "log"))
# both_model <- step(model_poisson, direction = "both")
# summary(model_poisson)
# final_model <- model_poisson

# model_nb <- glm.nb(Score ~ ., data = encoded_training_df)
# summary(model_nb)
# both_model <- step(model_nb, direction = "both")
# final_model <- both_model

# Supposons que 'future_matches_df' est le dataframe avec les futurs matchs
# Assurez-vous que 'future_matches_df' contient les mêmes colonnes que 'encoded_df', à l'exception de 'Score'
# Exemple : 
future_matches_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 10) %>% 
  filter(Wk == min(Wk)) %>% 
  select(-c(Wk, Date, Team_id, Team, Opponent_id, Opponent, Score_opp)) 
  

# Prédire sur les futurs matchsS
future_predictions <- predict(final_model, newdata = future_matches_df)

future_predictions <- ifelse(future_predictions < 0, 0.1, future_predictions)

# Afficher les prédictions
predictions_df <- encoded_df %>% 
  filter(is.na(Score),
         ymd(Date) - today() < 5) %>% 
  filter(Wk == min(Wk)) %>% 
  mutate(Score = future_predictions)
