library(dplyr)
library(tidyr)

# Fonction principale pour obtenir les derniers résultats pour chaque équipe
get_last_results_all_weeks <- function(df, side = NA_character_, nb_match = 3) {
  
  # Fonction interne pour obtenir les derniers résultats pour une semaine donnée
  last_results_function <- function(df, side, nb_match, current_week) {
    df_result <- df %>%
      filter(!is.na(result), Wk < current_week) %>%  # Filtrer les semaines précédentes
      select(Wk, Home = Home_id, Away = Away_id, result) %>%
      pivot_longer(
        cols = c(Home, Away),
        names_to = "Side",
        values_to = "Team_id"
      ) %>%
      mutate(Result_team = case_when(
        ((result == "H") & (Side == "Home")) | 
          ((result == "A") & (Side == "Away")) ~ "W", 
        ((result == "H") & (Side == "Away")) | 
          ((result == "A") & (Side == "Home")) ~ "L", 
        TRUE ~ "D"  # Utiliser TRUE pour les valeurs par défaut
      ))
    
    if (side %in% c("Home", "Away")) {
      df_result <- df_result %>%
        filter(Side == side)
    }
    
    res <- df_result %>%
      group_by(Team_id) %>%
      arrange(desc(Wk)) %>%  # Assurer un tri par ordre décroissant de la semaine
      slice_head(n = nb_match) %>%  # Sélectionner les derniers matchs
      mutate(J_label = paste0("J-", row_number())) %>%
      select(Team_id, Result_team, J_label) %>%
      pivot_wider(names_from = J_label, values_from = Result_team) 
    
    # Renommer les colonnes si un side est fourni
    if (!is.na(side) && side != "") {
      names(res)[-1] <- paste0(names(res)[-1], "_", side)  # Ajouter le suffixe au nom des colonnes
    }
    
    return(res)
  }
  
  # Obtenir toutes les semaines uniques
  weeks <- unique(df$Wk)
  
  # Appliquer last_results_function à chaque semaine et stocker les résultats
  results_list <- lapply(weeks, function(current_week) {
    last_results <- last_results_function(df, side, nb_match, current_week)
    last_results$Wk <- current_week  # Ajouter une colonne pour la semaine actuelle
    return(last_results)
  })
  
  # Combiner tous les résultats en un seul DataFrame
  final_results <- bind_rows(results_list) %>%
    mutate(across(everything(), ~ replace_na(.x, "D")))
  
  return(final_results)
}