from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Trouver le répertoire racine contenant "Prono_PL" et créer le chemin vers le fichier SQLite
root = Path(__file__).resolve().parent  # Partir du répertoire actuel du script

# Remonter dans les répertoires jusqu'à ce que l'on trouve "Prono_PL"
while not (root / 'Prono_PL').exists() and root != root.parent:
    root = root.parent

# Vérification et création du chemin du fichier SQLite
if (root / 'Prono_PL').exists():
    sqlite_file = root / 'Prono_PL' / 'my_database.db'
else:
    print("Répertoire 'Prono_PL' non trouvé")

system = platform.system()
if system == "Windows":
    print("Système détecté : Windows")
    service = Service(ChromeDriverManager().install())
elif system == "Linux":
    print("Système détecté : Linux (Raspberry Pi présumé)")
    service = Service('/usr/bin/chromedriver')
else:
    raise EnvironmentError(f"Système d'exploitation non supporté : {system}")

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=2560,1440")

# Utilisation de webdriver-manager pour gérer le chromedriver
driver = webdriver.Chrome(service=service, options=options)

try:
    # Naviguer vers l'URL cible
    url = "https://theanalyst.com/eu/competition/premier-league/fixtures"
    driver.get(url)

    WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                                             "button.DatePickerHeader-module_datepicker-header-date__wsJVr.DatePickerHeader-module_datepicker-header-date--clickable__v4vmf"))
    )

    # Trouver le bouton en utilisant ses classes
    button = driver.find_element(By.CSS_SELECTOR, 
        "button.DatePickerHeader-module_datepicker-header-date__wsJVr.DatePickerHeader-module_datepicker-header-date--clickable__v4vmf")
    
    # Récupérer le texte du bouton
    date_text = button.text

    # Convertir le texte en objet datetime
    date_object = datetime.strptime(date_text, "%b %d, %Y")

    # Reformatter en "YYYY-MM-DD"
    formatted_date = date_object.strftime("%Y-%m-%d")

    WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.FixtureTile-module_fixture-tile-link__GmKtI"))
    )
    # Trouver les éléments des liens des matchs
    elements = driver.find_elements(By.CSS_SELECTOR, "a.FixtureTile-module_fixture-tile-link__GmKtI")
    data = []

    # Parcourir les éléments pour extraire les informations
    for element in elements:
        try:
            WebDriverWait(element, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.FixtureTile-module_fixture-tile-team__IOR4n"))
            )
            # Récupérer les équipes
            team_elements = element.find_elements(By.CSS_SELECTOR, "div.FixtureTile-module_fixture-tile-team__IOR4n")
            if len(team_elements) >= 2:
                home_team = team_elements[0].text.strip()
                away_team = team_elements[1].text.strip()
            else:
                home_team = "Unknown"
                away_team = "Unknown"

            # Récupérer les probabilités si elles existent
            probabilities = element.find_elements(By.CSS_SELECTOR, "div.FixtureTile-module_probabilities-bar__8LfcA") 

            home_style = probabilities[0].get_attribute("style")
            draw_style = probabilities[1].get_attribute("style")
            away_style = probabilities[2].get_attribute("style")
        
            # Extraire le width depuis le style (par exemple: "width: 48%;")
            home_width = home_style.split("width:")[1].split(";")[0].strip().replace('%', '')
            draw_width = draw_style.split("width:")[1].split(";")[0].strip().replace('%', '')
            away_width = away_style.split("width:")[1].split(";")[0].strip().replace('%', '')

            # Convertir en float
            home_width = round(float(home_width))
            draw_width = round(float(draw_width))
            away_width = round(float(away_width))

            # Ajouter les informations dans la liste
            data.append({
                "Date": formatted_date,
                "H_team_name": home_team,
                "H_percent": home_width,
                "D_percent": draw_width,
                "A_percent": away_width,
                "A_team_name": away_team
            })
        except Exception as e:
            print(f"Erreur lors de l'extraction des données : {e}")
    
    # Créer un DataFrame pandas avec les données collectées
    df = pd.DataFrame(data)
    
    conn = sqlite3.connect(sqlite_file)

    try:
        # Charger les IDs des équipes depuis la table Table_teams
        query = """
        SELECT Opta_Name, Id
        FROM Table_teams
        """
        team_mapping = pd.read_sql_query(query, conn)

        # Créer un dictionnaire pour les correspondances des noms
        team_dict = dict(zip(team_mapping["Opta_Name"], team_mapping["Id"]))

        # Ajouter les IDs des équipes dans le DataFrame
        df["H_team"] = df["H_team_name"].map(team_dict)
        df["A_team"] = df["A_team_name"].map(team_dict)

        # Supprimer les colonnes des noms d'équipes, car elles ne sont plus nécessaires
        df = df[["Date", "H_team", "A_team", "H_percent", "D_percent", "A_percent"]]

        # Créer la table "Opta" si elle n'existe pas
        create_table_query = """
        CREATE TABLE IF NOT EXISTS Opta (
            Date TEXT,
            H_team TEXT,
            A_team TEXT,
            H_percent INTEGER,
            D_percent INTEGER,
            A_percent INTEGER,
            PRIMARY KEY (Date, H_team, A_team)
        );
        """
        conn.execute(create_table_query)

        # Insérer les données dans la table
        # Charger les données existantes pour détecter les conflits
        existing_data_query = """
            SELECT Date, H_team, A_team
            FROM Opta
        """
        existing_data = pd.read_sql_query(existing_data_query, conn)

        # Identifier les nouvelles lignes à insérer
        merged_df = df.merge(existing_data, on=["Date", "H_team", "A_team"], how="left", indicator=True)

        # Nouvelles lignes à insérer
        to_insert = merged_df[merged_df["_merge"] == "left_only"].drop(columns=["_merge"])

        # Lignes existantes à mettre à jour
        to_update = merged_df[merged_df["_merge"] == "both"].drop(columns=["_merge"])

        # Insérer les nouvelles lignes
        if not to_insert.empty:
            to_insert.to_sql("Opta", conn, if_exists="append", index=False)

        # Mettre à jour les lignes existantes
        if not to_update.empty:
            for _, row in to_update.iterrows():
                update_query = """
                    UPDATE Opta
                    SET H_percent = ?, D_percent = ?, A_percent = ?
                    WHERE Date = ? AND H_team = ? AND A_team = ?
                """
                conn.execute(update_query, (row["H_percent"], row["D_percent"], row["A_percent"], row["Date"], row["H_team"], row["A_team"]))

        conn.commit()

        print("Les données ont été insérées avec succès.")
    finally:
        # Fermer la connexion à la base de données
        conn.close()

finally:
    # Fermer le navigateur
    driver.quit()