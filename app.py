import streamlit as st
from chatbot import CollegeChatbot
import tempfile
import os

# ------------------------------
# Initialize chatbot
# ------------------------------
st.set_page_config(page_title="FRCRCE AI Chatbot", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    body {background-color: #f8fafc;}
    .stChatMessage {font-family: 'Poppins', sans-serif;}
    div[data-testid="stChatMessageUser"] {background-color: #dbeafe;}
    div[data-testid="stChatMessageAssistant"] {background-color: #f1f5f9;}
    .send-button {
        background-color: #2563eb;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 10px;
        cursor: pointer;
    }
    .send-button:hover {
        background-color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎓 FRCRCE Smart Campus Chatbot")
st.caption("Your one-stop for all FR-CRCE related questions :) .")

# Initialize chatbot and session history
if "chatbot" not in st.session_state:
    st.session_state.chatbot = CollegeChatbot()
if "messages" not in st.session_state:
    st.session_state.messages = []

chatbot = st.session_state.chatbot

# Display past chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------
# Chat input and file upload
# ------------------------------
query = st.chat_input("Type your question here...")

uploaded_file = st.file_uploader("📤 Upload an image (optional):", type=["png", "jpg", "jpeg"])
send_clicked = False

# Custom send button for uploaded image
if uploaded_file:
    st.success(f"✅ Image '{uploaded_file.name}' uploaded successfully.")
    send_clicked = st.button("📨 Send Image for Analysis")

# ------------------------------
# Handle queries
# ------------------------------
if query or send_clicked:
    with st.chat_message("user"):
        st.markdown(query if query else "📷 Image Query")

    st.session_state.messages.append({"role": "user", "content": query or "📷 Image Query"})

    image_path = None
    if uploaded_file and send_clicked:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.read())
            image_path = tmp.name

    with st.spinner("Thinking... 🤔"):
        response = chatbot.generate_response(query or "Extract text from the uploaded image", image_path=image_path)

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Delete temp image
    if image_path and os.path.exists(image_path):
        os.remove(image_path)
