from qdrant_client import QdrantClient, models
import fastembed
import numpy as np
import json
import random
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def get_unique_types(collection_name):
    client = QdrantClient(url=QDRANT_URL)


    if collection_name == "quotes":
        types = client.facet(
            collection_name = collection_name,
            key = "type"
        )
    elif collection_name == "steam_games":
        types = client.facet(
            collection_name = collection_name,
            key = "genres"
        )

    return [element.value for element in types.hits]


def get_result(user_query, collection_name, domain = None):

    client = QdrantClient(url=QDRANT_URL)

    model_name = "BAAI/bge-small-en-v1.5"

    if domain in get_unique_types(collection_name=collection_name):
        result_domain = "type" if collection_name == "quotes" else "genres"
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key=result_domain,
                    match=models.MatchValue(
                        value=domain
                    )
                )
            ]
        )
    else:
        filter = None

    if user_query is None:
        user_query = np.random.randn(client.get_embedding_size(model_name))
    else:
        user_query = models.Document(text=user_query, model=model_name)


    search_result = client.query_points(
        collection_name=collection_name,
        query=user_query,
        query_filter = filter,
        timeout = 30
    ).points


    if search_result:
        return search_result
    else:
        return None

if __name__ == "__main__":

    #query = input("What kind of quote would you like today?\nEnter your query here and press 'Enter': ")

    query = None

    domains = get_unique_types()

    #domain = input(f"What type of quote would you like? We have quotes from {domains}\nEnter your query here and press 'Enter': ")
    domain = None
    quote = get_result(query, domain)

    print(quote.payload["quote"])
    print(quote.payload["source"].strip(",").title())
