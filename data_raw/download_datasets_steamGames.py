import pandas as pd
import os


FILE_NAME = "steam_games.json"


def calculate_review_score(row):
    
    try:
        score = (row["positive"]/(row["positive"]+row["negative"]))*100
        score = round(score, 2)

    except Exception as error:
        print(error)
        score = 0
    
    return score




if os.path.exists(FILE_NAME):
    print("Data is already saved! Loading data...\n")
    steam_games = pd.read_json(FILE_NAME)
else:
    print("Data does not exist yet, downloading data...")
    steam_games = pd.read_parquet("hf://datasets/FronkonGames/steam-games-dataset/data/train-00000-of-00001.parquet")



steam_games["review_score"] = steam_games.apply(calculate_review_score, axis=1)



columns_to_keep = {"name", "price", "detailed_description", "short_description", "supported_languages", "windows", "mac", "linux", "metacritic_score", "user_score", "review_score", "developers", "publishers", "genres", "categories"}

columns_to_delete = [set(steam_games.columns)-columns_to_keep]

if len(columns_to_delete) > 0:
    for col in columns_to_delete:
        steam_games.drop(col, axis = 1, inplace = True)

if len(set(steam_games.columns)-columns_to_keep) == 0:
    print("successfully deleted unused cols!")
else:
    print("delete not successful")



steam_games.to_json(FILE_NAME, orient = "records", indent = 2)
print("data saved!")