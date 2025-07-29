library(DBI)
library(RSQLite)
library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

# Connexion à la base SQLite
sqlite_file <- file.path(root, "Prono_PL", "my_database.db")
con <- dbConnect(RSQLite::SQLite(), dbname = sqlite_file)

# Création des tables si elles n'existent pas
dbExecute(con, "
CREATE TABLE IF NOT EXISTS Stats_players (
  Player TEXT,
  Shirt_Number INTEGER,
  Nation TEXT,
  Position TEXT,
  Age TEXT,
  Minutes INTEGER,
  Goals INTEGER,
  Assists INTEGER,
  Penalty_Kicks_Made INTEGER,
  Penalty_Kicks_Attempted INTEGER,
  Shots_Total INTEGER,
  Shots_on_Target INTEGER,
  Yellow_Cards INTEGER,
  Red_Cards INTEGER,
  Touches INTEGER,
  Tackles INTEGER,
  Interceptions INTEGER,
  Blocks INTEGER,
  xG_Expected_Goals REAL,
  npxG_NonPenalty_xG REAL,
  xAG_Exp_Assisted_Goals REAL,
  ShotCreating_Actions INTEGER,
  GoalCreating_Actions INTEGER,
  Passes_Completed INTEGER,
  Passes_Attempted INTEGER,
  Pass_Completion_Perc REAL,
  Progressive_Passes INTEGER,
  Carries INTEGER,
  Progressive_Carries INTEGER,
  TakeOns_Attempted INTEGER,
  Successful_TakeOns INTEGER,
  Total_Passing_Distance INTEGER,
  Progressive_Passing_Distance INTEGER,
  Passes_Completed_Short INTEGER,
  Passes_Attempted_Short INTEGER,
  Pass_Completion_Perc_Short REAL,
  Passes_Completed_Medium INTEGER,
  Passes_Attempted_Medium INTEGER,
  Pass_Completion_Perc_Medium REAL,
  Passes_Completed_Long INTEGER,
  Passes_Attempted_Long INTEGER,
  Pass_Completion_Perc_Long REAL,
  xA_Expected_Assists REAL,
  Key_Passes INTEGER,
  Passes_into_Final_Third INTEGER,
  Passes_into_Penalty_Area INTEGER,
  Crosses_into_Penalty_Area INTEGER,
  Liveball_Passes INTEGER,
  Deadball_Passes INTEGER,
  Passes_from_Free_Kicks INTEGER,
  Through_Balls INTEGER,
  Switches INTEGER,
  Crosses INTEGER,
  Throwins_Taken INTEGER,
  Corner_Kicks INTEGER,
  Inswinging_Corner_Kicks INTEGER,
  Outswinging_Corner_Kicks INTEGER,
  Straight_Corner_Kicks INTEGER,
  Passes_Offside INTEGER,
  Passes_Blocked INTEGER,
  Tackles_Won INTEGER,
  Tackles_Def_3rd INTEGER,
  Tackles_Mid_3rd INTEGER,
  Tackles_Att_3rd INTEGER,
  Dribblers_Tackled INTEGER,
  Dribbles_Challenged INTEGER,
  Perc_of_Dribblers_Tackled REAL,
  Challenges_Lost INTEGER,
  Shots_Blocked INTEGER,
  TklInt INTEGER,
  Clearances INTEGER,
  Errors INTEGER,
  Touches_Def_Pen INTEGER,
  Touches_Def_3rd INTEGER,
  Touches_Mid_3rd INTEGER,
  Touches_Att_3rd INTEGER,
  Touches_Att_Pen INTEGER,
  Touches_LiveBall INTEGER,
  Successful_TakeOn_Perc REAL,
  Times_Tackled_During_TakeOn INTEGER,
  Tackled_During_TakeOn_Percentage REAL,
  Total_Carrying_Distance INTEGER,
  Progressive_Carrying_Distance INTEGER,
  Carries_into_Final_Third INTEGER,
  Carries_into_Penalty_Area INTEGER,
  Miscontrols INTEGER,
  Dispossessed INTEGER,
  Passes_Received INTEGER,
  Progressive_Passes_Rec INTEGER,
  Second_Yellow_Card INTEGER,
  Fouls_Committed INTEGER,
  Fouls_Drawn INTEGER,
  Offsides INTEGER,
  Penalty_Kicks_Won INTEGER,
  Penalty_Kicks_Conceded INTEGER,
  Own_Goals INTEGER,
  Ball_Recoveries INTEGER,
  Aerials_Won INTEGER,
  Aerials_Lost INTEGER,
  Perc_of_Aerials_Won REAL,
  team TEXT,
  game TEXT
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Prono_history (
  Date TEXT,
  H_team TEXT,
  A_team TEXT,
  H_percent REAL,
  D_percent REAL,
  A_percent REAL,
  score_pred TEXT,
  score_pred_percent REAL,
  PRIMARY KEY (Date, H_team, A_team)
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Opta (
  Date TEXT,
  H_team TEXT,
  A_team TEXT,
  H_percent INTEGER,
  D_percent INTEGER,
  A_percent INTEGER,
  PRIMARY KEY (Date, H_team, A_team)
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Table_teams (
  Id TEXT,
  Squad TEXT,
  Gender TEXT,
  Comp TEXT,
  Other_Names TEXT,
  Venue_Name TEXT,
  latitude REAL,
  longitude REAL,
  Abv TEXT,
  Opta_Name TEXT,
  Color TEXT
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Book_history (
  H_team TEXT,
  A_team TEXT,
  Site TEXT,
  H REAL,
  D REAL,
  A REAL,
  H_percent REAL,
  D_percent REAL,
  A_percent REAL
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Calendrier (
  Wk INTEGER,
  Day TEXT,
  Date TEXT,
  Time TEXT,
  Home TEXT,
  score_home INTEGER,
  score_away INTEGER,
  Away TEXT,
  Attendance TEXT,
  Referee TEXT,
  result TEXT,
  link TEXT,
  id TEXT,
  Home_id TEXT,
  Away_id TEXT
);
")

dbExecute(con, "
CREATE TABLE IF NOT EXISTS Classement (
  Id TEXT,
  J0 INTEGER
);
")

# Déconnexion
dbDisconnect(con)
