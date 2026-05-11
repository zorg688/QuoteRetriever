import streamlit as st
import random



from src import infer_from_database as infer

st.title("Quote Retriever")

st.session_state.visibility = "visible"
st.session_state.disabled = False
st.session_state.placeholder = "A quote about inner strength"

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False
    st.session_state.placeholder = "A quote about inner strength"



def get_domains():

    domains = infer.get_unique_types(collection_name="quotes")

    domains.append("surprise me")
    return domains

def get_quote_from_database(query, domain):

    quote = infer.get_result(user_query=query, collection_name="quotes", domain=domain)

    return quote

def print_answer(quotes):
    quote = random.choice(quotes)

    try:
        st.header(f"Your quote from the {quote.payload["type"]} domain:")
        st.subheader(quote.payload["quote"]) 

        source_text = "- from the " + quote.payload["type"] + " " + quote.payload["source"].strip(",")
        st.write(r"$\textsf{\Large" + source_text.title()+ "}$")
    except:
        st.header(f"Sorry, but there is no quote for your question from the domain {domain}")


query = st.text_input(
    r"$\textsf{\small What kind of quote would you like today? Comedic, movie or philosophical quotes? }$",
    label_visibility=st.session_state.visibility,
    disabled=st.session_state.disabled,
    placeholder=st.session_state.placeholder,
)

domain = st.radio(
    "What type of quote would you like to receive?",
    get_domains(),
    index = None
)

col1, col2 = st.columns(2)

if col1.button("Run query", type= "primary"):

    quote_get_state = st.spinner("Awaiting query...")

    quotes = get_quote_from_database(query, domain)

    quote_final_state = st.spinner("Received quote")

    print_answer(quotes)

if col2.button("I am feeling lucky", icon ="🎲"):
    quote_get_state = st.spinner("Awaiting random query...")

    quotes = get_quote_from_database(None, None)
    
    quote_final_state = st.spinner("Received quote")

    print_answer(quotes)



