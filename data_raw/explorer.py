import json

import pandas as pd




with open("quotes.json", "r") as file:
    data = json.load(file)

all_types = set()

for element in data:
    if element["type"] not in all_types:
        print(element["quote"])
        print(element["source"])
        print(element["type"])
        print("-"*60)
        all_types.add(element["type"])