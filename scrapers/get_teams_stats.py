import sqlite3
import pandas as pd
from understatapi import UnderstatClient
from database.get_cloud_db import DB_PATH


# ── Transform ─────────────────────────────────────────────────────────────────

def team_to_df(team: dict) -> pd.DataFrame:
    rows = []
    for match in team['history']:
        date_str = match['date'][:10].replace('-', '')
        rows.append({
            'id':               f"{team['id']}_{date_str}",
            'date':             match['date'],
            'id_team':          team['id'],
            'title':            team['title'],
            'h_a':              match['h_a'],
            'xG':               match['xG'],
            'xGA':              match['xGA'],
            'npxG':             match['npxG'],
            'npxGA':            match['npxGA'],
            'ppda_att':         match['ppda']['att'],
            'ppda_def':         match['ppda']['def'],
            'ppda_allowed_att': match['ppda_allowed']['att'],
            'ppda_allowed_def': match['ppda_allowed']['def'],
            'deep':             match['deep'],
            'deep_allowed':     match['deep_allowed'],
            'scored':           match['scored'],
            'missed':           match['missed'],
            'result':           match['result'],
            'wins':             match['wins'],
            'draws':            match['draws'],
            'loses':            match['loses'],
            'pts':              match['pts'],
            'xpts':             match['xpts'],
            'npxGD':            match['npxGD'],
        })
    return pd.DataFrame(rows)

def teams_to_df(teams: list[dict]) -> pd.DataFrame:
    return pd.concat([team_to_df(m) for m in teams], ignore_index=True)


# ── Main function ─────────────────────────────────────────────────────────────

def get_teams_stats(season: str = "2025"):

    understat = UnderstatClient()
    team_data = understat.league(league="EPL").get_team_data(season=season)

    df = teams_to_df(list(team_data.values()))

    con = sqlite3.connect(DB_PATH)
    existing_ids = pd.read_sql_query("SELECT id FROM teams_stats;", con)["id"].tolist()
    new_rows = df[~df["id"].isin(existing_ids)]
    if new_rows.empty:
        print("No new rows to insert")
    else:
        new_rows.to_sql("teams_stats", con, if_exists="append", index=False)
        print(f"{len(new_rows)} new rows inserted")
    con.close()

if __name__ == "__main__":
    get_teams_stats()