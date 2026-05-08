from qdrant_client import QdrantClient, models
import fastembed
import numpy as np
import json
import random
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def get_unique_types():
    client = QdrantClient(url=QDRANT_URL)

    collection_name = "quotes"

    types = client.facet(
        collection_name = collection_name,
        key = "type"
    )

    return [element.value for element in types.hits]


def get_quote(user_query, domain = None):

    client = QdrantClient(url=QDRANT_URL)

    collection_name = "quotes"

    model_name = "BAAI/bge-small-en-v1.5"


    if domain in get_unique_types():
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

    if user_query is None:
        user_query = np.random.randn(client.get_embedding_size(model_name))
    else:
        user_query = models.Document(text=query, model=model_name)


    search_result = client.query_points(
        collection_name=collection_name,
        query=user_query,
        query_filter = filter
    ).points

    if search_result:
        return random.choice(search_result)
    else:
        return None

if __name__ == "__main__":

    #query = input("What kind of quote would you like today?\nEnter your query here and press 'Enter': ")

    query = None

    domains = get_unique_types()

    #domain = input(f"What type of quote would you like? We have quotes from {domains}\nEnter your query here and press 'Enter': ")
    domain = None
    quote = get_quote(query, domain)

    print(quote.payload["quote"])
    print(quote.payload["source"].strip(",").title())
