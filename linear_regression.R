library(caret)

source("preprocessing.R")

set.seed(42)  # Pour la reproductibilité
trainIndex <- createDataPartition(encoded_df$Score, p = 0.8, list = FALSE)
trainData <- encoded_df[trainIndex, ]
testData <- encoded_df[-trainIndex, ]

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