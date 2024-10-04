source("linear_regression_pred.R")

results_list <- list()

# Calculer les probabilités pour chaque Score dans Wk
for (i in 1:nrow(predictions_df)) {
  lambda <- predictions_df$Score[i]
  g_values <- 0:10
  probabilities <- dpois(g_values, lambda)
  results_list[[i]] <- data.frame(Team_id = predictions_df$Team_id[i], g = g_values, Probability = probabilities)
}

# Combiner les résultats dans un seul dataframe
results_df <- bind_rows(results_list)

pivoted_df <- results_df %>%
  pivot_wider(names_from = g, values_from = Probability, names_prefix = "g_")

data <- predictions_df %>% 
  filter(Dist == 0) %>% 
  left_join(pivoted_df, by="Team_id") %>% 
  left_join(pivoted_df, by=c("Opponent_id" = "Team_id"), suffix = c("_h", "_a"))

# Extraire les colonnes finissant par _h et _a
home_columns <- data %>% select(ends_with("_h"))
away_columns <- data %>% select(ends_with("_a"))

# Initialiser des vecteurs pour stocker les résultats
max_values <- numeric(nrow(data))
max_coords <- matrix(NA, nrow = nrow(data), ncol = 2)
upper_sums <- numeric(nrow(data))
lower_sums <- numeric(nrow(data))
diagonal_sums <- numeric(nrow(data))

# Boucle sur chaque ligne
for (i in 1:nrow(data)) {
  # Extraire les vecteurs pour la ligne i
  home_vector <- as.numeric(home_columns[i, ])
  away_vector <- as.numeric(away_columns[i, ])
  
  # Calculer le produit matriciel
  result_matrix <- t(t(home_vector)) %*% away_vector
  
  # Trouver la valeur maximale et ses coordonnées
  max_index <- which.max(result_matrix)
  max_coords[i, ] <- arrayInd(max_index, dim(result_matrix))
  max_values[i] <- result_matrix[max_coords[i, ]]
  
  # Calculer les probabilités pour upper, lower et diagonal
  upper_sums[i] <- sum(result_matrix[upper.tri(result_matrix)])
  lower_sums[i] <- sum(result_matrix[lower.tri(result_matrix)])
  diagonal_sums[i] <- sum(diag(result_matrix))
  
  # Stocker le résultat dans la liste
  results_list[[i]] <- result_matrix
}

# Ajouter les résultats au dataframe d'origine
data <- data %>%
  mutate(score_pred = paste0(max_coords[, 1] - 1, "-", max_coords[, 2] - 1),
         `score_pred_%` = max_values * 100,
         `H(%)` = lower_sums * 100,
         `D(%)` = diagonal_sums * 100,
         `A(%)` = upper_sums * 100) %>% 
  select(Date, Time, H_team = Team_id, `H(%)`, `D(%)`, `A(%)`, A_team = Opponent_id, score_pred, `score_pred_%`) %>% 
  mutate_if(is.numeric, ~round(., 2))
