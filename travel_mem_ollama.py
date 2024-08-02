import os
import streamlit as st
import requests
from mem0 import Memory
#Read OpenAI API key from .env file


st.title("AI based Travel Advisor")
st.caption("Powered by Llama 3.1 and Streamlit")

ollama_endpoint = st.text_input("Enter Ollama API endpoint", value="http://localhost:11434")

config = {
    "vector_store":{
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333
        }
    },

}
memory = Memory.from_config(config)

st.sidebar.title("Username")
previous_user_id = st.session_state.get("previous_user_id", None)
user_id = st.sidebar.text_input("Enter username")

if user_id != previous_user_id:
    st.session_state.messages = []
    st.session_state.previous_user_id = user_id

if st.sidebar.button("View History"):
    if user_id:
        memories = memory.get_all(user_id=user_id)
        if memories:
            st.sidebar.write(f"History for **{user_id}**:")
            for memory in memories:
                st.sidebar.write(f"- {memory['text']}")
        else:
            st.sidebar.write(f"No history found for **{user_id}**.")
    else:
        st.sidebar.error("Please enter a username to view history.")        

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("Clear History"):
    if user_id:
        memory.clear(user_id=user_id)
        st.sidebar.write(f"History for **{user_id}** cleared.")
    else:
        st.sidebar.error("Please enter a username to clear history.")

prompt = st.text_input("Where would you like to teleport?")

if prompt and user_id:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    relevant_memories = memory.search(query=prompt, user_id=user_id)
    context = "History:\n"
    for memory in relevant_memories:
        context += f"- {memory['text']}\n"

    full_prompt = f"You are a travel agent with access to historical conversations. {context}\nHuman: {prompt}\nAI:"

    response = requests.post(
        f"{ollama_endpoint}/api/generate",
        json={
            "model": "llama3.1",
            "prompt": full_prompt,
            "stream": False
        }
    )

    if response.status_code == 200:
        answer = response.json()['response']

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

        memory.add(user_id=user_id, text=prompt, answer=answer, metadata={"role": "user"})
    else:
        st.error(f"Error: Unable to get response from Ollama. Status code: {response.status_code}")

elif not user_id:
    st.error("Please enter a username to start the chat")