import streamlit as st
from openai import OpenAI
import pyodbc
import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# SQL Server connection parameters
db_server = os.getenv("DB_SERVER")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# SQL Server connection string
conn_str = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={db_server};"
    f"Database={db_name};"
    f"Uid={db_user};"
    f"Pwd={db_password};"
    f"Encrypt=no;"
    f"TrustServerCertificate=no;"
)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Function to check if the question is pet-related using OpenAI
def is_pet_related(message):
    try:
        check = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a classifier that answers only with 'yes' or 'no'. Respond only with 'yes' if the message is related to pets (animals like dogs, cats, birds, etc). Otherwise respond 'no'."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=0
        )
        reply = check.choices[0].message.content.strip().lower()
        return reply == "yes"
    except Exception as e:
        print("Error during pet check:", e)
        return True  # Default to true if unsure

# Save chat to database
def save_to_db(user_message, bot_response):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ChatHistory (UserInput, AssistantResponse)
            VALUES (?, ?)
        """, (user_message, bot_response))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ DB Error:", e)

# Retrieve chat history
def get_chat_history():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT UserInput, AssistantResponse, Timestamp FROM ChatHistory ORDER BY Timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("DB Error:", e)
        return []

# Streamlit UI
st.set_page_config(page_title="Pet ChatBot 🐾", page_icon="🐶")
st.title("🐶 Pet ChatBot")
st.write("Ask me something about pets:")

user_input = st.text_input("")

if user_input:
    with st.spinner("Thinking..."):
        if is_pet_related(user_input):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_input}]
                )
                reply = response.choices[0].message.content.strip()
                st.success(reply)
                save_to_db(user_input, reply)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
        else:
            st.warning("⚠️ Please ask pet-related questions only.")

# Option to view chat history
if st.checkbox("Show chat history"):
    history = get_chat_history()
    for user_msg, bot_msg, ts in history:
        st.markdown(f"**🕒 {ts.strftime('%Y-%m-%d %H:%M:%S')}**")
        st.markdown(f"👤 You: {user_msg}")
        st.markdown(f"🤖 Bot: {bot_msg}")
        st.markdown("---")
