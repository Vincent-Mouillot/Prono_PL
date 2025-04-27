# Charger les packages nécessaires
library(gt)
library(dplyr)

df_model <- dbGetQuery(
  con,
  "SELECT
      h.Date,
      c.Time,
      t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
      'Model' AS Site,
      h.H_percent,
      h.D_percent,
      h.A_percent
   FROM Prono_history AS h
   JOIN Table_teams AS t1 ON h.H_team = t1.Id
   JOIN Table_teams AS t2 ON h.A_team = t2.Id
   JOIN Calendrier AS c ON c.Home_id = h.H_team
                        AND c.Away_id = h.A_team
   WHERE c.result IS NULL;"
)


df_opta <- dbGetQuery(
  con,
  "SELECT
      h.Date,
      c.Time,
      t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
      'Opta' AS Site,
      o.H_percent,
      o.D_percent,
      o.A_percent
   FROM Prono_history AS h
   JOIN Table_teams AS t1 ON h.H_team = t1.Id
   JOIN Table_teams AS t2 ON h.A_team = t2.Id
   JOIN Calendrier AS c ON c.Home_id = h.H_team
                        AND c.Away_id = h.A_team
   JOIN Opta AS o ON o.H_team = h.H_team
                        AND o.A_team = h.A_team
   WHERE c.result IS NULL;"
)

df_compl <- dbGetQuery(
  con,
  "SELECT r.Date,
  r.Time,
  t1.Other_Names AS Home_Team_Name,
      t1.Color AS Home_color,
      t2.Other_Names AS Away_Team_Name,
      t2.Color AS Away_color,
          p.Site,
          p.H_percent,
          p.D_percent,
          p.A_percent,
          r.result
      FROM Calendrier AS r
      JOIN Book_history AS p ON p.H_team = r.Home_id 
        AND  p.A_team = r.Away_id
      JOIN Table_teams AS t1 ON p.H_team = t1.Id
   JOIN Table_teams AS t2 ON p.A_team = t2.Id
      WHERE r.result IS NULL
  AND Site IN ('Winamax', 'Parionssport');"
)

# Supposons que df_compl est votre data frame initial
df <- df_model %>% 
  bind_rows(df_opta) %>% 
  bind_rows(df_compl)

# Créer les colonnes de barres
df$H_Bar <- sprintf(
  '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: %s; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
  df$Home_color,
  df$H_percent,
  df$H_percent
)

df$D_Bar <- sprintf(
  '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: #D3D3D3; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
  df$D_percent,
  df$D_percent
)

df$A_Bar <- sprintf(
  '<div style="display: flex; align-items: center; height: 20px;">
     <div style="background-color: %s; width: %s%%; height: 100%%;"></div>
     <span style="margin-left: 6px; line-height: 20px;">%s%%</span>
   </div>',
  df$Away_color,
  df$A_percent,
  df$A_percent
)

# Créer une colonne unique pour le regroupement
df$Match <- paste(df$Date, " ", df$Time, " - ", df$Home_Team_Name, "vs", df$Away_Team_Name)

# Créer la table gt avec des groupes de lignes
gt_table <- gt(df %>% 
                 select(Match, Site, H_Bar, D_Bar, A_Bar),
               groupname_col = "Match") %>%
  tab_header(
    title = "Match Results with Bars"
  ) %>%
  cols_label(
    H_Bar = md("**Home Bar**"),
    D_Bar = md("**Draw Bar**"),
    A_Bar = md("**Away Bar**")
  ) %>%
  fmt_markdown(columns = c(H_Bar, D_Bar, A_Bar))

# Afficher la table
print(gt_table)

