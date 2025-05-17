import streamlit as st
from minio import Minio
from minio.error import S3Error
import json
import time
import string
import random
import io

minio_client = Minio(
    "play.min.io",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    secure=True
)

BUCKET_NAME = "group-chat-app"
USERS_FILE = "users.json"

def initialize_bucket():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as e:
        print(f"Error occurred: {e}")

def load_users():
    try:
        response = minio_client.get_object(BUCKET_NAME, USERS_FILE)
        users_data = response.read().decode('utf-8')
        return json.loads(users_data)
    except S3Error:
        return {}

def save_users(users):
    json_data = json.dumps(users).encode('utf-8')
    minio_client.put_object(
        BUCKET_NAME,
        USERS_FILE,
        io.BytesIO(json_data),
        len(json_data)
    )

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        'password': password,
        'groups': []
    }
    save_users(users)
    return True

def authenticate_user(username, password):
    users = load_users()
    user_data = users.get(username)
    if user_data:
        return user_data.get('password') == password
    return False

def add_group_to_user(username, group_id):
    users = load_users()
    if username in users:
        users[username]['groups'].append(group_id)
        save_users(users)

def get_user_groups(username):
    users = load_users()
    return users.get(username, {}).get('groups', [])

def create_group():
    group_id = ''.join(random.choices(string.ascii_uppercase, k=6))
    group_data = {
        'messages': [],
        'created_at': time.time()
    }
    save_group_data(group_id, group_data)
    return group_id

def join_group(group_id, username):
    try:
        minio_client.stat_object(BUCKET_NAME, f"{group_id}.json")
        add_group_to_user(username, group_id)
        return True
    except S3Error:
        return False

def send_message(group_id, username, message):
    group_data = get_group_data(group_id)
    group_data['messages'].append({
        'username': username,
        'message': message,
        'timestamp': time.time()
    })
    save_group_data(group_id, group_data)

def get_messages(group_id):
    group_data = get_group_data(group_id)
    return group_data.get('messages', [])

def save_group_data(group_id, data):
    json_data = json.dumps(data).encode('utf-8')
    minio_client.put_object(
        BUCKET_NAME,
        f"{group_id}.json",
        io.BytesIO(json_data),
        len(json_data)
    )

def get_group_data(group_id):
    try:
        response = minio_client.get_object(BUCKET_NAME, f"{group_id}.json")
        return json.loads(response.read().decode('utf-8'))
    except S3Error:
        return {'messages': []}

def main():
    st.set_page_config(page_title="Chatty Bro", page_icon="💬", layout="centered")

    st.markdown("""
<style>
.stApp {
    background-color: #07e9ed;
    font-family: 'Arial', sans-serif;
}
.stTextInput > div > div > input {
    background-color: #ffffff;
    color: #000000;
    border-radius: 5px;
    border: 1px solid #cccccc;
}
.stButton > button {
    background-color: #007bff;
    color: white;
    border-radius: 5px;
    border: none;
    padding: 10px 24px;
    transition: all 0.05s ease;
}
.stButton > button:hover {
    background-color: #0056b3;
}
.chat-message {
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    display: inline-block;
    max-width: 70%;
}
.user-message {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
    float: right;
}
.other-message {
    background-color: #e9ecef;
    color: #1b1e21;
    border: 1px solid #d6d8db;
    float: left;
}
</style>
""", unsafe_allow_html=True)

    st.title("Chatty Bro")

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'group_id' not in st.session_state:
        st.session_state.group_id = ''
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'view' not in st.session_state:
        st.session_state.view = 'selection'  # options: 'selection', 'login', 'register'

    if not st.session_state.logged_in:
        if st.session_state.view == 'selection':
            if st.button("Login", key="login_button"):
                st.session_state.view = 'login'
            if st.button("Register", key="register_button"):
                st.session_state.view = 'register'

        if st.session_state.view == 'login':
            st.write("### Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_submit"):
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.view = 'selection'
                else:
                    st.error("Invalid username or password")
            if st.button("Back", key="login_back"):
                st.session_state.view = 'selection'

        if st.session_state.view == 'register':
            st.write("### Register")
            new_username = st.text_input("New Username", key="register_username")
            new_password = st.text_input("New Password", type="password", key="register_password")
            if st.button("Register", key="register_submit"):
                if register_user(new_username, new_password):
                    st.session_state.logged_in = True
                    st.session_state.username = new_username
                    st.session_state.view = 'selection'
                    st.success("Registration successful! You are now logged in.")
                else:
                    st.error("Username already exists")
            if st.button("Back", key="register_back"):
                st.session_state.view = 'selection'

    if st.session_state.logged_in:
        st.write(f"Welcome, {st.session_state.username}!")

        user_groups = get_user_groups(st.session_state.username)
        if user_groups:
            st.write("Your Groups:")
            for group in user_groups:
                if st.button(group, key=f"group_{group}"):
                    st.session_state.group_id = group

        if not st.session_state.group_id:
            col1, col2 = st.columns(2)
            with col1:
                group_id = st.text_input("Enter group code to join:", key="group_code_input")
                if st.button("Join Group", key="join_group_button"):
                    if join_group(group_id, st.session_state.username):
                        st.session_state.group_id = group_id
                    else:
                        st.error("Invalid group code")
            with col2:
                if st.button("Create New Group", key="create_group_button"):
                    new_group_id = create_group()
                    add_group_to_user(st.session_state.username, new_group_id)
                    st.session_state.group_id = new_group_id
                    st.success(f"New group created! Code: {new_group_id}")
    
        if st.session_state.group_id:
            st.rerun()
            st.write(f"Group Code: {st.session_state.group_id}")
            message = st.text_input("Type your message:", key="message_input")
            if st.button("Send", key="send_button"):
                if message:
                    send_message(st.session_state.group_id, st.session_state.username, message)

            messages = get_messages(st.session_state.group_id)
            for msg in messages:
                if msg['username'] == st.session_state.username:
                    st.markdown(f"<div class='chat-message user-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message other-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)

            time.sleep(1)

if __name__ == "__main__":
    initialize_bucket()
    main()
