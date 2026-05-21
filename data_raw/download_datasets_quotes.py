#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "huggingface_hub",
# ]
# ///
"""Download and merge movie, funny, and philosopher quote datasets from Hugging Face."""

import pandas as pd  # type: ignore[import-not-found]

movie_quotes = pd.read_csv("hf://datasets/ygorgeurts/movie-quotes/movie_quotes.csv")

funny_quotes = pd.read_json("hf://datasets/Khalida1w/funny_quotes/funnyQuotes.jsonl", lines=True)

philo_quotes = pd.read_csv("hf://datasets/datastax/philosopher-quotes/philosopher-quotes.csv")


philo_cols = list(philo_quotes.columns)

col1, col2 = philo_cols.index("author"), philo_cols.index("quote")


philo_cols[col1], philo_cols[col2] = philo_cols[col2], philo_cols[col1]
philo_quotes = philo_quotes[philo_cols]

philo_quotes["type"] = "philosopher"

funny_quotes["type"] = "author"

final_data = pd.DataFrame(columns = ["quote", "source", "type"])

for data in [movie_quotes, funny_quotes, philo_quotes]:

    if "movie" in list(data.columns):
        data.rename(columns={'movie': 'source'}, inplace=True)
    elif "author" in list(data.columns):
        data.rename(columns={'author': 'source'}, inplace=True)


    cols_to_delete = list(set(data.columns)-{"quote", "source", "type"})

    if len(cols_to_delete) > 0:
        for col in cols_to_delete:
            data.drop(col, axis = 1, inplace = True)
    final_data = pd.concat([final_data, data])

final_data["type"] = final_data["type"].replace("tv", "tv show")

final_data.to_json("quotes.json", orient = "records", indent = 2)
