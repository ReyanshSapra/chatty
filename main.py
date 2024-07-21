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

try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
except S3Error as e:
    print(f"Error occurred: {e}")

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
    st.set_page_config(page_title="Chatty", page_icon="💬", layout="centered")

    st.markdown("""
<style>
.stApp {
    background-color: #444444;
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
    transition: all 0.3s ease;
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

    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'group_id' not in st.session_state:
        st.session_state.group_id = ''

    if not st.session_state.username:
        st.session_state.username = st.text_input("Enter your name:")

    if st.session_state.username:
        if not st.session_state.group_id:
            col1, col2 = st.columns(2)
            with col1:
                group_id = st.text_input("Enter group code to join:")
                if st.button("Join Group"):
                    if join_group(group_id, st.session_state.username):
                        st.session_state.group_id = group_id
                    else:
                        st.error("Invalid group code")
            with col2:
                if st.button("Create New Group"):
                    new_group_id = create_group()
                    st.session_state.group_id = new_group_id
                    st.success(f"New group created! Code: {new_group_id}")

        if st.session_state.group_id:
            st.write(f"Group Code: {st.session_state.group_id}")
            message = st.text_input("Type your message:")
            if st.button("Send"):
                if message:
                    send_message(st.session_state.group_id, st.session_state.username, message)

            messages = get_messages(st.session_state.group_id)
            for msg in messages:
                if msg['username'] == st.session_state.username:
                    st.markdown(f"<div class='chat-message user-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message other-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)

            time.sleep(1)
            st.experimental_rerun()

if __name__ == "__main__":
    main()
