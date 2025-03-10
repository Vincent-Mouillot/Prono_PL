# Charger les packages nécessaires
library(gt)
library(dplyr)

# Supposons que df_compl est votre data frame initial
df <- df_compl %>%
  filter(Site %in% c('Winamax', 'Parionssport'))

# Créer les colonnes de barres
df$H_Bar <- sprintf(
  '<div style="background-color: #4c72b0; width: %s%%; height: 20px;"></div>',
  df$H_percent
)

df$D_Bar <- sprintf(
  '<div style="background-color: #55a868; width: %s%%; height: 20px;"></div>',
  df$D_percent
)

df$A_Bar <- sprintf(
  '<div style="background-color: #c44e52; width: %s%%; height: 20px;"></div>',
  df$A_percent
)

# Créer une colonne unique pour le regroupement
df$Match <- paste(df$H_team, "vs", df$A_team)

# Créer la table gt avec des groupes de lignes
gt_table <- gt(df) %>%
  tab_header(
    title = "Match Results with Bars"
  ) %>%
  # tab_row_group(
  #   group = Match,
  #   label = function(value) {
  #     paste("Match:", value)
  #   }
  # ) %>%
  cols_label(
    H_Bar = md("**Home Bar**"),
    D_Bar = md("**Draw Bar**"),
    A_Bar = md("**Away Bar**")
  ) %>%
  fmt_markdown(columns = c(H_Bar, D_Bar, A_Bar))

# Afficher la table
print(gt_table)

