from qdrant_client import QdrantClient, models

import fastembed

import numpy as np

import json

import random


def get_unique_types():
    client = QdrantClient(url="http://localhost:6333")

    collection_name = "quotes"

    types = client.facet(
        collection_name = collection_name,
        key = "type"
    )

    print(types)

    return [element.value for element in types.hits]


def get_quote(query, domain = None):

    client = QdrantClient(url="http://localhost:6333")

    collection_name = "quotes"

    model_name = "BAAI/bge-small-en-v1.5"

    if domain is not None and domain != "surprise me":
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(
                        value=domain
                    )
                )
            ]
        )
    else:
        filter = None


    search_result = client.query_points(
        collection_name=collection_name,
        query=models.Document(text=query, model=model_name),
        query_filter = filter
    ).points

    if search_result:
        return random.choice(search_result)
    else:
        return None

if __name__ == "__main__":

    query = input("What kind of quote would you like today?\nEnter your query here and press 'Enter': ")

    domains = get_unique_types()

    domain = input(f"What type of quote would you like? We have quotes from {domains}\nEnter your query here and press 'Enter': ")
    quote = get_quote(query, domain)

    print(quote.payload["source"].strip(","))
