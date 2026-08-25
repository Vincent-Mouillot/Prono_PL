import re
import pandas as pd
import numpy as np

shared_cols = ['id', 'datetime']

def neutralize_col(col):
    col = re.sub(r'_(h|a)_', '_', col)
    col = re.sub(r'_(h|a)$', '', col)
    col = re.sub(r'^(h|a)_', '', col)
    return col

# Features

team_features = {
    'ranking'  : ['diff_rank'],
    'ewp'      : ['ewp_saison', 'ewp_window'],
    'power'    : ['off_power', 'def_power'],
    'target'   : ['xg'],
}

opp_features = {
    'ewp'   : ['ewp_saison', 'ewp_window'],
    'power' : ['off_power', 'def_power'],
}

DC_POWER_COLS = ["off_power", "def_power", "off_power_opp", "def_power_opp"]

NON_FEATURE_COLS = ["id", "datetime", "xg", "is_home"]

# Flatten to use in function
features_flat     = [f for group in team_features.values() for f in group]
opp_features_flat = [f for group in opp_features.values() for f in group]


def build_side(df : pd.DataFrame, home_map, away_map, is_home):
    own_map, opp_map = (home_map, away_map) if is_home else (away_map, home_map)
    
    result = df[shared_cols].copy()
    result['is_home'] = int(is_home)
    
    # features pf the team
    for feat in features_flat:
        if feat in own_map:
            result[feat] = df[own_map[feat]]
    
    # features of the opponent
    for feat in opp_features_flat:
        if feat in opp_map:
            result[f'{feat}_opp'] = df[opp_map[feat]]

    if 'gamma' in df.columns:
        result['log_gamma_home'] = np.log(df['gamma']) * int(is_home)
    
    return result

def to_log_powers(df_long: pd.DataFrame) -> pd.DataFrame:
    """Pour un arbre c'est un no-op (transfo monotone → mêmes splits).
    Pour un GLM à lien log, c'est ce qui rend la structure DC exactement linéaire."""
    for col in DC_POWER_COLS:
        df_long[f"log_{col}"] = np.log(df_long[col].clip(lower=1e-6))
    return df_long.drop(columns=DC_POWER_COLS)

def preprocessing_function(df_calendar : pd.DataFrame):
    df = df_calendar.copy()

    # mapping neutralised
    home_map = {neutralize_col(c): c for c in df.columns if re.search(r'(_h_|_h$)', c)}
    away_map = {neutralize_col(c): c for c in df.columns if re.search(r'(_a_|_a$)', c)}

    df_long = pd.concat([build_side(df, home_map, away_map, True), build_side(df, home_map, away_map, False)]).reset_index(drop=True)

    return to_log_powers(df_long)

if __name__ == "__main__":
    calendar = pd.read_csv("df_calendar.csv")
    print(preprocessing_function(calendar))