import chromadb
import os
import random
import streamlit as st
import string
import uuid

from benbot.core import (
  get_session,
  rag,
  run_llm,
  stream_llm,
  update_session
)
from captcha.image import ImageCaptcha
from dotenv import load_dotenv
from tinydb import TinyDB

load_dotenv()


CHAT_LIMIT = int(os.getenv("CHAT_LIMIT", 20))
LTM_SYSTEM_MESSAGE = os.getenv("LTM_SYSTEM_MESSAGE", "Summarize the conversation.")
SYSTEM_MESSAGE = os.getenv("SYSTEM_MESSAGE", "You are a helpful assistant.")

chroma_client = chromadb.PersistentClient(path=f"_data/chroma")
db = TinyDB(f"_data/db.json")
docs = chroma_client.get_collection("benbot")

# source: https://discuss.streamlit.io/t/streamlit-captcha-integration/38318
# define the costant
length_captcha = 4
width_captcha = 200
height_captcha = 150


# define the function for the captcha control
def captcha_control():
    #control if the captcha is correct
    if 'controllo' not in st.session_state or st.session_state['controllo'] == False:
        # st.title("Only one robot at a time! 🤖")
        
        # define the session state for control if the captcha is correct
        st.session_state['controllo'] = False
        col1, col2 = st.columns(2)
        
        # define the session state for the captcha text because it doesn't change during refreshes 
        if 'Captcha' not in st.session_state:
                st.session_state['Captcha'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length_captcha))
        print("the captcha is: ", st.session_state['Captcha'])
        
        #setup the captcha widget
        image = ImageCaptcha(width=width_captcha, height=height_captcha)
        data = image.generate(st.session_state['Captcha'])
        col1.image(data)
        capta2_text = col2.text_area('Enter captcha text', height=30)
        
        
        if st.button("Verify the code"):
            print(capta2_text, st.session_state['Captcha'])
            capta2_text = capta2_text.replace(" ", "")
            # if the captcha is correct, the controllo session state is set to True
            if st.session_state['Captcha'].lower() == capta2_text.lower().strip():
                del st.session_state['Captcha']
                col1.empty()
                col2.empty()
                st.session_state['controllo'] = True
                st.experimental_rerun() 
            else:
                # if the captcha is wrong, the controllo session state is set to False and the captcha is regenerated
                st.error("🚨 Il codice captcha è errato, riprova")
                del st.session_state['Captcha']
                del st.session_state['controllo']
                st.experimental_rerun()
        else:
            #wait for the button click
            st.stop()


def paywall_handler(content=None, user=None, db=None, docs=None):
    # get the bot's response from the LLM
    llm_stream = stream_llm(messages=[
        {"role": "system", "content": "No matter what the user says, you will pretend you didn't hear it because you were busy doing other things. Make it light-hearted, play dumb, aloof, and redirect them to the contact page: https://benmcdougal.com/connect"},
        {"role": "user", "content": content}
    ])

    response = ""
    for token in llm_stream:
        response += token
        yield token


def handler(content=None, user=None, db=None, docs=None):
    # get user information from db, create if it does not exist
    user_info = get_session(session=user, db=db)

    # append the user's message to the user's message history
    user_info["messages"].append({"role": "user", "content": content})

    # truncate the message history to the chat limit
    if len(user_info["messages"]) > CHAT_LIMIT:
        user_info["messages"] = user_info["messages"][-CHAT_LIMIT:]

    # get the bot's response from the LLM
    llm_stream = stream_llm(messages=[
        {"role": "system", "content": SYSTEM_MESSAGE + "\n\n" + rag(content, docs=docs) + f"\n\nSummary of my conversation with the user:\n{user_info['ltm']}"},
        # {"role": "system", "content": SYSTEM_MESSAGE + f"\n\nSummary of my conversation with {user}:\n{user_info['ltm']}"},
    ] + user_info["messages"])

    response = ""
    for token in llm_stream:
        response += token
        yield token

    # append the bot's response to the user's message history
    user_info["messages"].append({"role": "assistant", "content": response})

    # truncate the message history to the chat limit
    if len(user_info["messages"]) > CHAT_LIMIT:
        user_info["messages"] = user_info["messages"][-CHAT_LIMIT:]

    # create a long term memory (ltm) summary of the conversation (helps with conversational persistance)
    ltm = run_llm(messages=[
        {"role": "system", "content": LTM_SYSTEM_MESSAGE},
        {"role": "user", "content": "\n".join([f"{msg['role']}: {msg['content']}" for msg in user_info["messages"]])}
    ])

    # update the user's information in the db
    update_session(session=user, db=db, messages=user_info["messages"], ltm=ltm)


def main():
    if "user" not in st.session_state:
        st.session_state.user = f"streamlit:{str(uuid.uuid4())}"

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # st.info(st.session_state.user)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # response = st.write_stream(response_generator())
            # st.write(response)

            user = get_session(session=st.session_state.user, db=db)

            if len(user["messages"]) >=5:
                response = st.write_stream(paywall_handler(content=prompt, user=st.session_state.user, db=db, docs=docs))
            else:
                response = st.write_stream(handler(content=prompt, user=st.session_state.user, db=db, docs=docs))

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


# WORK LIKE MULTIPAGE APP         
if 'controllo' not in st.session_state or st.session_state['controllo'] == False:
    captcha_control()
else:
    main()