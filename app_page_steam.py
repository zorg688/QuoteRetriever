import streamlit as st
import random


from src import infer_from_database as infer
from src import generate_answer as gen_answer

st.title("Game Recommender")

st.session_state.visibility = "visible"
st.session_state.disabled = False
st.session_state.placeholder = "A game about fighting god"

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False
    st.session_state.placeholder = "A game about fighting god"



def get_genres():

    genres = infer.get_unique_types("steam_games")
    genres.append("surprise me")
    return genres



def get_game_from_database(query, genre):

    game = infer.get_result(user_query=query, domain=genre, collection_name= "steam_games")
    return game



def print_answer(games, domain):


    

    try:
        game = random.choice(games)
        st.header("Your game of the type " + ",".join(game.payload["genres"]) + ":")
        st.subheader(game.payload["name"]) 
        st.write(game.payload["detailed_description"])
    except:
        st.header(f"Sorry, but there is no game for your query. However, these migth still be interesting: ") 




def use_ollama(query, games, domain):

    if games:

        st.subheader(f"For your query '{query}' I recommend to try these:")
        with st.spinner("Collecting game recommendations..."):
            for game in games:
                response = gen_answer.generate_answer(query, game)

                if game.payload["genres"]:
                    st.write(f"- {game.payload["name"]}, a {",".join(game.payload["genres"])}: {round(game.score*100, 2)}% fit")
                else:
                    st.write(f"- {game.payload["name"]}: {round(game.score*100, 2)}% fit")
                with st.expander("See the reason why this fits"):
                    if game.payload["detailed_description"]:
                        st.write(f"- Description: \n{game.payload["detailed_description"]}")
                    st.write(response)

        
        st.write("That's all for now :)")
    else:
        st.header(f"Sorry, but there is no game for your question in genre {domain}")
    



query = st.text_input(
    r"$\textsf{\small What kind of game would you like to try? }$",
    label_visibility=st.session_state.visibility,
    disabled=st.session_state.disabled,
    placeholder=st.session_state.placeholder,
)

domain = st.radio(
    "What type of game would you like to try??",
    get_genres(),
    index = None
)

col1, col2, col3 = st.columns(3)

if col1.button("Run query", type= "primary"):

    game_get_state = st.spinner("Awaiting query...")

    games = get_game_from_database(query, domain)

    game_final_state = st.spinner("Received game")
    print_answer(games, domain)



if col2.button("I am feeling lucky", icon ="🎲"):
    game_get_state = st.spinner("Awaiting random query...")

    games = get_game_from_database(None, None)
    
    game_final_state = st.spinner("Received game")
    print_answer(games, domain)

if col3.button("Test the new AI generated Answer here!", icon = "💻"):
    games = get_game_from_database(query, domain)

    use_ollama(query, games, domain)


