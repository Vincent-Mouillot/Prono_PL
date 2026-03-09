from understatapi import UnderstatClient
import pandas as pd

understat = UnderstatClient()

# Matchs PL 2025
match_data = understat.league(league="EPL").get_match_data(season="2025")

def match_to_df(match: dict) -> pd.DataFrame:
    is_played = match['isResult']
    forecast = match.get('forecast')

    return pd.DataFrame([{
        'id':       match['id'],
        'datetime': match['datetime'],
        'h_team':   match['h']['short_title'],
        'a_team':   match['a']['short_title'],
        'goals_h':  int(match['goals']['h']) if is_played else None,
        'goals_a':  int(match['goals']['a']) if is_played else None,
        'xg_h':     float(match['xG']['h']) if is_played else None,
        'xg_a':     float(match['xG']['a']) if is_played else None,
        'proba_w':  round(float(forecast['w']) * 100) if forecast else None,
        'proba_d':  round(float(forecast['d']) * 100) if forecast else None,
        'proba_l':  round(float(forecast['l']) * 100) if forecast else None,
        'result':   ('H' if int(match['goals']['h']) > int(match['goals']['a'])
                     else 'A' if int(match['goals']['h']) < int(match['goals']['a'])
                     else 'D') if is_played else None
    }])

# Pour une liste de matchs
def matches_to_df(matches: list[dict]) -> pd.DataFrame:
    return pd.concat([match_to_df(m) for m in matches], ignore_index=True)

print(matches_to_df(match_data))