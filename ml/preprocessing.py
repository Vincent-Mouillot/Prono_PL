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
    'ewp'      : ['ewp_saison', 'ewp_window'],
    'power'    : ['off_power'],
    'creation' : ['deep'],
    'target'   : ['npxg'],
}

opp_features = {
    'ewp'      : ['ewp_saison', 'ewp_window'],
    'power'    : ['def_power'],
    'creation' : ['deep_allowed'],
}

LOG_COLS = ["off_power", "def_power_opp", "deep", "deep_allowed_opp"]

NON_FEATURE_COLS = ["id", "datetime", "npxg", "is_home"]

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
    Pour un GLM à lien log, ça rend la structure DC exactement linéaire pour
    off_power/def_power_opp, et ça traite ppda_opp comme un facteur
    multiplicatif du même genre plutôt qu'un terme linéaire additif."""
    for col in LOG_COLS:
        df_long[f"log_{col}"] = np.log(df_long[col].clip(lower=1e-6))
    return df_long.drop(columns=LOG_COLS)

def add_interactions(df_long: pd.DataFrame) -> pd.DataFrame:
    """log_deep + log_deep_allowed_opp, replacing the two individual terms: only
    the interaction enters the model, capturing whether a team's own chance
    creation compounds specifically against sides that leak deep completions,
    without also giving each side an independent additive effect."""
    df_long["log_deep_product"] = df_long["log_deep"] + df_long["log_deep_allowed_opp"]
    return df_long.drop(columns=["log_deep", "log_deep_allowed_opp"])

def preprocessing_function(df_calendar : pd.DataFrame):
    df = df_calendar.copy()

    # mapping neutralised
    home_map = {neutralize_col(c): c for c in df.columns if re.search(r'(_h_|_h$)', c)}
    away_map = {neutralize_col(c): c for c in df.columns if re.search(r'(_a_|_a$)', c)}

    df_long = pd.concat([build_side(df, home_map, away_map, True), build_side(df, home_map, away_map, False)]).reset_index(drop=True)

    df_long = to_log_powers(df_long)
    return add_interactions(df_long)

if __name__ == "__main__":
    calendar = pd.read_csv("df_calendar.csv")
    print(preprocessing_function(calendar))