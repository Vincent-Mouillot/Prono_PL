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

# Find the root directory containing "Prono_PL" and build the path to the SQLite file
root = Path(__file__).resolve().parent  # Start from the script's current directory

# Walk up the directories until "Prono_PL" is found
while not (root / 'Prono_PL').exists() and root != root.parent:
    root = root.parent

# Check and build the SQLite file path
if (root / 'Prono_PL').exists():
    sqlite_file = root / 'Prono_PL' / 'my_database.db'
else:
    print("'Prono_PL' directory not found")

system = platform.system()
if system == "Windows":
    print("Detected system: Windows")
    service = Service(ChromeDriverManager().install())
elif system == "Linux":
    print("Detected system: Linux (assumed Raspberry Pi)")
    service = Service('/usr/bin/chromedriver')
else:
    raise EnvironmentError(f"Unsupported operating system: {system}")

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=2560,1440")

# Use webdriver-manager to manage the chromedriver
driver = webdriver.Chrome(service=service, options=options)

try:
    # Navigate to the target URL
    url = "https://theanalyst.com/eu/competition/premier-league/fixtures"
    driver.get(url)

    WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                             "button.DatePickerHeader-module_datepicker-header-date__wsJVr.DatePickerHeader-module_datepicker-header-date--clickable__v4vmf"))
    )

    # Find the button using its classes
    button = driver.find_element(By.CSS_SELECTOR,
        "button.DatePickerHeader-module_datepicker-header-date__wsJVr.DatePickerHeader-module_datepicker-header-date--clickable__v4vmf")

    # Get the button's text
    date_text = button.text

    # Convert the text into a datetime object
    date_object = datetime.strptime(date_text, "%b %d, %Y")

    # Reformat as "YYYY-MM-DD"
    formatted_date = date_object.strftime("%Y-%m-%d")

    WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.FixtureTile-module_fixture-tile-link__GmKtI"))
    )
    # Find the match link elements
    elements = driver.find_elements(By.CSS_SELECTOR, "a.FixtureTile-module_fixture-tile-link__GmKtI")
    data = []

    # Iterate over the elements to extract the information
    for element in elements:
        try:
            WebDriverWait(element, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.FixtureTile-module_fixture-tile-team__IOR4n"))
            )
            # Get the teams
            team_elements = element.find_elements(By.CSS_SELECTOR, "div.FixtureTile-module_fixture-tile-team__IOR4n")
            if len(team_elements) >= 2:
                home_team = team_elements[0].text.strip()
                away_team = team_elements[1].text.strip()
            else:
                home_team = "Unknown"
                away_team = "Unknown"

            # Get the probabilities if they exist
            probabilities = element.find_elements(By.CSS_SELECTOR, "div.FixtureTile-module_probabilities-bar__8LfcA")

            home_style = probabilities[0].get_attribute("style")
            draw_style = probabilities[1].get_attribute("style")
            away_style = probabilities[2].get_attribute("style")

            # Extract the width from the style (e.g. "width: 48%;")
            home_width = home_style.split("width:")[1].split(";")[0].strip().replace('%', '')
            draw_width = draw_style.split("width:")[1].split(";")[0].strip().replace('%', '')
            away_width = away_style.split("width:")[1].split(";")[0].strip().replace('%', '')

            # Convert to float
            home_width = round(float(home_width))
            draw_width = round(float(draw_width))
            away_width = round(float(away_width))

            # Add the information to the list
            data.append({
                "Date": formatted_date,
                "H_team_name": home_team,
                "H_percent": home_width,
                "D_percent": draw_width,
                "A_percent": away_width,
                "A_team_name": away_team
            })
        except Exception as e:
            print(f"Error while extracting data: {e}")

    # Build a pandas DataFrame from the collected data
    df = pd.DataFrame(data)

    conn = sqlite3.connect(sqlite_file)

    try:
        # Load the team IDs from the Table_teams table
        query = """
        SELECT Opta_Name, Id
        FROM Table_teams
        """
        team_mapping = pd.read_sql_query(query, conn)

        # Build a dictionary for the name mapping
        team_dict = dict(zip(team_mapping["Opta_Name"], team_mapping["Id"]))

        # Add the team IDs to the DataFrame
        df["H_team"] = df["H_team_name"].map(team_dict)
        df["A_team"] = df["A_team_name"].map(team_dict)

        # Drop the team name columns, no longer needed
        df = df[["Date", "H_team", "A_team", "H_percent", "D_percent", "A_percent"]]

        # Create the "Opta" table if it doesn't exist
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

        # Insert the data into the table
        # Load the existing data to detect conflicts
        existing_data_query = """
            SELECT Date, H_team, A_team
            FROM Opta
        """
        existing_data = pd.read_sql_query(existing_data_query, conn)

        # Identify the new rows to insert
        merged_df = df.merge(existing_data, on=["Date", "H_team", "A_team"], how="left", indicator=True)

        # New rows to insert
        to_insert = merged_df[merged_df["_merge"] == "left_only"].drop(columns=["_merge"])

        # Existing rows to update
        to_update = merged_df[merged_df["_merge"] == "both"].drop(columns=["_merge"])

        # Insert the new rows
        if not to_insert.empty:
            to_insert.to_sql("Opta", conn, if_exists="append", index=False)

        # Update the existing rows
        if not to_update.empty:
            for _, row in to_update.iterrows():
                update_query = """
                    UPDATE Opta
                    SET H_percent = ?, D_percent = ?, A_percent = ?
                    WHERE Date = ? AND H_team = ? AND A_team = ?
                """
                conn.execute(update_query, (row["H_percent"], row["D_percent"], row["A_percent"], row["Date"], row["H_team"], row["A_team"]))

        conn.commit()

        print("Data successfully inserted.")
    finally:
        # Close the database connection
        conn.close()

finally:
    # Close the browser
    driver.quit()
