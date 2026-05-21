"""
Script for generating the LLM answer locally with a specified model. 
The model is loaded at startup of the container to reduce inference time
This is so far only used for the steam game recommendation tool
"""

import os
from ollama import Client

client = Client(host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))

MODEL_NAME = "qwen3.5:9b"

# Pre-load the model into GPU memory at import time
print(f"Pre-loading {MODEL_NAME} into memory...")
client.generate(model=MODEL_NAME, prompt="", keep_alive=-1)
print(f"{MODEL_NAME} loaded.")

def generate_answer(query, game):

    model_name = MODEL_NAME

    game_string = game.payload["name"] + "; Description:" + game.payload["detailed_description"] + "; Genres:" + ",".join(game.payload["genres"])

    prompt = f""" The question is a query for a recommendation for a steam game. The context is a fitting game selected from a database.
    Explain why the game fits the query based only on the context.

    Question:
    {query}

    Context:
    {game_string}

    Your answer must always start with 'This game is recommended for your query, because: ' and list the reasons as bullet points
    
    Double check that this form is adhered by before finalizing your answer
    """

    print("message received, generating answer...")

    response = client.generate(model=model_name, prompt=prompt, think=False)

    return response.response