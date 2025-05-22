import streamlit as st
import requests

# Backend API endpoints
local = "http://localhost:8000"
remote = "https://english-agent-demo.onrender.com/"
API_BASE = remote
REGISTER_URL = f"{API_BASE}/register"
LOGIN_URL = f"{API_BASE}/login"
STREAM_URL = f"{API_BASE}/stream"

# App configuration
st.set_page_config(page_title="English Chatbot", page_icon="💬")
st.title("💬 English Learning Chatbot - Streaming Only")

# Sidebar: Registration/Login/Logout
st.sidebar.title("User Authentication")

# Session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.api_key = ""
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# Registration form
if not st.session_state.logged_in:
    with st.sidebar.expander("Register"):
        reg_username = st.text_input("Username", key="reg_user")
        reg_password = st.text_input("Password", type="password", key="reg_pass")
        native_language = st.text_input("Native Language", key="reg_lang")
        lang_code = st.text_input("Language Code (e.g., en, es)", key="reg_code")
        if st.button("Register"):
            payload = {
                "username": reg_username,
                "password": reg_password,
                "native_language": native_language,
                "lang_code": lang_code
            }
            res = requests.post(REGISTER_URL, json=payload)
            if res.status_code == 200:
                st.success("Registration successful! Please log in.")
            else:
                detail = res.json().get("detail", "Registration failed.")
                st.error(detail)

# Login form
if not st.session_state.logged_in:
    with st.sidebar.expander("Login"):
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            res = requests.post(LOGIN_URL, data={"username": login_user, "password": login_pass})
            if res.status_code == 200:
                data = res.json()
                st.session_state.api_key = data.get("api_key")
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("Login failed: " + res.json().get("detail", "Invalid credentials."))

# Logout
if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.api_key = ""
        st.session_state.username = ""
        st.session_state.messages.clear()
        st.rerun()

# Chat interface (streaming only)
if st.session_state.logged_in:
    st.subheader(f"Hello, {st.session_state.username}! Chat with Manisha (Streaming)")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    prompt = st.chat_input("Type your message here...")
    if prompt:
        # Append and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        # Prepare headers and payload
        headers = {"x-api-key": st.session_state.api_key}
        payload = {"query": prompt}

        # Streaming response from FastAPI
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_text = ""
            try:
                res = requests.post(
                    STREAM_URL,
                    json=payload,
                    headers=headers,
                    stream=True,
                )
                if res.status_code == 200:
                    for line in res.iter_lines():
                        if line:
                            chunk = line.decode('utf-8').replace("data: ", "")
                            response_text += chunk
                            response_placeholder.markdown(response_text + "▌")
                    response_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Streaming error: {e}")
