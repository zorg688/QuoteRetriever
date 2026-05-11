import os
from ollama import Client

client = Client(host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))

def generate_answer(query, game):

    model_name = "gemma4:e4b"

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

    response = client.generate(model=model_name, prompt=prompt)

    return response.response