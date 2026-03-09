from understatapi import UnderstatClient
import pandas as pd

understat = UnderstatClient()

# Matchs PL 2025
player_data = understat.league(league="EPL").get_player_data(season="2025")

def player_to_df(player: dict) -> pd.DataFrame:
    return pd.DataFrame([{
        'id':           player['id'],
        'player_name':  player['player_name'],
        'games':        player['games'],
        'time':         player['time'],
        'goals':        player['goals'],
        'xG':           player['xG'],
        'assists':      player['assists'],
        'xA':           player['xA'],
        'shots':        player['shots'],
        'key_passes':   player['key_passes'],
        'yellow_cards': player['yellow_cards'],
        'red_cards':    player['red_cards'],
        'position':     player['position'],
        'team_title':   player['team_title'],
        'npg':          player['npg'],
        'npxG':         player['npxG'],
        'xGChain':      player['xGChain'],
        'xGBuildup':    player['xGBuildup'],
    }])

# Pour une liste de matchs
def players_to_df(players: list[dict]) -> pd.DataFrame:
    return pd.concat([player_to_df(m) for m in players], ignore_index=True)

print(players_to_df(player_data))
#print(player_data)