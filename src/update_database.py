from qdrant_client import QdrantClient, models

import fastembed

import numpy as np

import json

import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

def initialise_database(client, collection_name):
    model_name = "BAAI/bge-small-en-v1.5"
    

    # Create a collection with three named vectors
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name), distance=models.Distance.COSINE)
    )
    client.create_payload_index(
        collection_name=collection_name,
        field_name="type",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )

    print("collection created")

    #load data
    with open("../data_raw/quotes.json", "r") as file:
        payload = json.load(file)

    vector_embeds = [models.Document(text=data["quote"], model=model_name) for data in payload]

    ids = [index for index, _ in enumerate(payload)]

    client.upload_collection(
        collection_name="quotes",
        vectors=vector_embeds,
        ids=ids,
        payload=payload,
    )

def update_payloads(client, collection_name):

    payload_to_update= "type"
    old_value = "tv"
    new_value= "tv show"

    client.set_payload(
    collection_name=collection_name,
    payload={
        payload_to_update: new_value,
    },
    points=models.Filter(
        must=[
            models.FieldCondition(
                key=payload_to_update,
                match=models.MatchValue(value=old_value),
            ),
        ],
    ),
)


if __name__ == "__main__":

    client = QdrantClient(url=QDRANT_URL)

    collection_name = "quotes"

    if client.collection_exists(collection_name=collection_name) == False:
        initialise_database(client, collection_name)

    else:
        print("collection already exists, updating database...")

        #update_payloads(client, collection_name)