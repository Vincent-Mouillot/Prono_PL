library(caret)

source("preprocessing.R")

encoded_training_df <- encoded_df %>% 
  filter(!is.na(Score))

set.seed(42)  # Pour la reproductibilité
trainIndex <- createDataPartition(encoded_training_df$Score, p = 0.8, list = FALSE)
trainData <- encoded_training_df[trainIndex, ]
testData <- encoded_training_df[-trainIndex, ]

# Créer un modèle de régression linéaire pour prédire "Score"
model <- lm(Score ~ ., data = trainData)

# Résumé du modèle
summary(model)

# Prédire sur l'ensemble de test
predictions <- predict(model, newdata = testData)

# Évaluer la performance du modèle (Mean Squared Error - MSE)
mse <- mean((testData$Score - predictions)^2)
cat("Mean Squared Error (MSE) :", mse, "\n")

# Afficher les prédictions et les scores réels
data.frame(Real_Score = testData$Score, Predicted_Score = predictions)