import streamlit as st


from src import infer_from_database as infer

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

col1, col2 = st.columns(2)

if col1.button("Run query", type= "primary"):

    query_get_state = st.spinner("Awaiting query...")

    game = get_game_from_database(query, domain)

    query_final_state = st.spinner("Received game")

    try:
        st.header("Your game of the type" + ",".join(game.payload["genres"]) + ":")
        st.subheader(game.payload["name"]) 

        #source_text = "- from the " + game.payload["type"] + " " + game.payload["source"].strip(",")
        #st.write(r"$\textsf{\Large" + source_text.title()+ "}$")
    except:
        st.header(f"Sorry, but there is no game for your question from the domain {domain}")
if col2.button("I am feeling lucky", icon ="🎲"):
    game_get_state = st.spinner("Awaiting random query...")

    game = get_game_from_database(None, None)
    
    game_final_state = st.spinner("Received game")

    try:

        st.header("Your game of the type" + ",".join(game.payload["genres"]) + ":")
        st.subheader(game.payload["name"]) 

        #source_text = "- from the " + game.payload["type"] + " " + game.payload["source"].strip(",")
        #st.write(r"$\textsf{\Large" + source_text.title()+ "}$")
    except Exception as e:

        st.header(f"Sorry, but there is no game for your question from the domain {domain}")
        st.write(e)
        st.write(game.payload)


