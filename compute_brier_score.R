library(data.table)

brier_score <- function(df, mean=FALSE){
  one_hot <- as.data.table(model.matrix(~ result - 1, data = df))
  setnames(one_hot, old = colnames(one_hot), new = gsub("result", "result_", colnames(one_hot)))
  df <- cbind(df, one_hot) %>% 
    select(-result)
  
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