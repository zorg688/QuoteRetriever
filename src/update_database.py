from qdrant_client import QdrantClient, models

import json

import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DATA_PATH = "../data_raw"

def generate_embeddings(collection_name, payload, model_name):

    print("Embedding data...")
    
    if collection_name == "quotes":
        return [models.Document(text=data["quote"], model=model_name) for data in payload]
    elif collection_name == "steam_games":
        texts_for_embedding = [data["name"] + ":" + data["short_description"] + ":" + ",".join(data["genres"]) for data in payload]

        return [models.Document(text= single_texts, model=model_name) for single_texts in texts_for_embedding]
    else:
        raise Exception(f"No valid collection exists for collection {collection_name}!")



def initialise_database(client, collection_name, file_name):
    model_name = "BAAI/bge-small-en-v1.5"
    
    #load data
    print("loading data...")
    with open("/".join([DATA_PATH, file_name]), "r") as file:
        payload = json.load(file)

    # Create a collection
    print("creating collection...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name), distance=models.Distance.COSINE)
    )

    print("indexing payload...")
    if collection_name == "quotes":
        index_names = [("type", models.PayloadSchemaType.KEYWORD)]
    elif collection_name == "steam_games":
        index_names = [
            ("genres", models.PayloadSchemaType.KEYWORD),
            ("review_score", models.PayloadSchemaType.FLOAT),
            ("price", models.PayloadSchemaType.FLOAT),
            ("windows", models.PayloadSchemaType.BOOL),
            ("mac", models.PayloadSchemaType.BOOL),
            ("linux", models.PayloadSchemaType.BOOL),
        ]
    else:
        index_names = None


    if index_names is not None:
        for field_name, field_schema in index_names:
            print(field_name)
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
                timeout = 30
            )

    print("collection created")

    vector_embeds = generate_embeddings(collection_name=collection_name, payload=payload, model_name=model_name)

    ids = [index for index, _ in enumerate(payload)]

    client.upload_collection(
        collection_name=collection_name,
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

def scan_drive():

    files = os.listdir(DATA_PATH)

    return [file for file in files if file.endswith(".json")]



if __name__ == "__main__":

    files =scan_drive()

    collection_names = [file.replace(".json", "") for file in files]

    client = QdrantClient(url=QDRANT_URL)

    
    for collection_name, file_name in zip(collection_names, files):
        if client.collection_exists(collection_name) == False:
            print("Initializing database...")
            initialise_database(client, collection_name, file_name)

        else:
            print("collection already exists")

        #update_payloads(client, collection_name)