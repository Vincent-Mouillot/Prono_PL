calculate_previous_week_avg <- function(df, sc, join_key) {
  
  # Fonction interne pour calculer la moyenne des semaines précédentes
  get_previous_avg <- function(data, current_week) {
    data %>%
      filter(Wk < current_week) %>%
      group_by(Team_id) %>%  # Toujours groupé par Team_id
      summarise(!!paste0("avg_", sc) := mean(.data[[sc]], na.rm = TRUE)) %>%
      mutate(Wk = current_week)
  }
  
  # Calcul des moyennes pour chaque semaine
  weeks <- unique(df$Wk)
  avg_scores_by_week <- map_dfr(weeks, ~ get_previous_avg(df, .x))
  
  # Fusionner les moyennes avec les données originales
  final_df <- df %>%
    left_join(avg_scores_by_week, by = setNames("Team_id", join_key) %>% c("Wk" = "Wk")) %>%
    mutate(across(starts_with("avg_"), ~ replace_na(.x, 0)))
  
  return(final_df)
}

# Exemple d'utilisation
# calculate_previous_week_avg(df, "Score", "Opponent_id")
