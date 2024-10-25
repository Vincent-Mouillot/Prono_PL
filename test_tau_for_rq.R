library(ggplot2)

taus <- c(0.5, 0.65, 0.75, 0.9)
# set.seed(42)  # Fixer une graine pour la reproductibilité
random_indices <- sample(nrow(encoded_training_df), 20)

# Créer un nouveau dataframe sans les lignes sélectionnées
encoded_training_df_test <- encoded_training_df[-random_indices, ]
encoded_test_df_test <- encoded_training_df[random_indices, ]

pred_df <- data.frame(Actual = encoded_test_df_test$Score)

for (tau in taus) {
  model <- rq(Score ~ ., data = encoded_training_df_test, tau = tau)
  pred_df[paste("Tau", tau, sep = "_")] <- predict(model, newdata = encoded_test_df_test)

  mae <- mean(abs(pred_df[[paste("Tau", tau, sep = "_")]] - pred_df$Actual))
  print(paste("Tau:", tau, " - MAE:", mae))
}

# Créer une visualisation des résultats
ggplot(pred_df, aes(x = Actual)) +
  geom_point(aes(y = Tau_0.5), color = "blue") +
  geom_point(aes(y = Tau_0.65), color = "green") +
  geom_point(aes(y = Tau_0.75), color = "red") +
  geom_point(aes(y = Tau_0.9), color = "orange") +
  labs(title = "Comparaison des prédictions pour différentes valeurs de tau", 
       y = "Prédictions") +
  theme_minimal()

