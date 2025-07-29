import sqlite3
import pandas as pd

# Chemin vers la base de données
db_path = "my_database.db"

# Connexion à la base de données
conn = sqlite3.connect(db_path)

# Charger la table Table_teams
table_teams_query = "SELECT * FROM Table_teams"
table_teams = pd.read_sql_query(table_teams_query, conn)
try: 
    table_teams = table_teams.drop(columns=["Opta_Name"])
except:
        print("No Opta names column")

# Création du DataFrame des noms à mapper
data = {
    "Opta_Name": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
        "Leeds", "Liverpool", "Man City", "Man Utd", "Newcastle",
        "Nottm Forest", "Sunderland", "Tottenham", "West Ham", "Wolves"
    ],
    "Other_Names": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", 
        "Brighton & Hove Albion", "Chelsea", "Burnley", "Crystal Palace",
        "Everton", "Fulham", "Leeds United", "Liverpool", 
        "Manchester City", "Manchester United", "Newcastle United", 
        "Nottingham Forest", "Sunderland", "Tottenham Hotspur", 
        "West Ham United", "Wolverhampton Wanderers"
    ]
}
mapping_df = pd.DataFrame(data)

# Effectuer le join avec table_teams
updated_table_teams = table_teams.merge(mapping_df, on="Other_Names", how="left")

# Mettre à jour la table Table_teams dans la base de données
updated_table_teams.to_sql("Table_teams", conn, if_exists="replace", index=False)

# Vérifier les résultats
print("Table mise à jour avec succès.")
print(updated_table_teams.head())

# Fermer la connexion
conn.close()