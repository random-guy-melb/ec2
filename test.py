import streamlit as st

st.set_page_config(page_title="Purple Chatbot", page_icon="💬", layout="wide")

# Custom CSS for purple theme
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}

    .custom-banner {
        background: linear-gradient(135deg, #A78BFA 0%, #9333EA 100%);
        padding: 20px;
        border-radius: 0 0 15px 15px;
        margin: -70px -70px 30px -70px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .banner-title {
        color: white;
        font-size: 28px;
        font-weight: 600;
        text-align: center;
    }

    .main {
        background-color: #FAF5FF;
    }

    .stButton button {
        background-color: #F3E8FF;
        color: #6B21A8;
        border-radius: 20px;
        border: 1px solid #E9D5FF;
        font-weight: 500;
    }

    .stButton button:hover {
        background-color: #E9D5FF;
        border-color: #A78BFA;
    }
    </style>
    """, unsafe_allow_html=True)

# Banner
st.markdown("""
    <div class="custom-banner">
        <div class="banner-title">💬 AI Assistant</div>
    </div>
    """, unsafe_allow_html=True)

# Quick suggestions
SUGGESTIONS = [
    "Show high-priority incidents from today",
    "Summarize latest Jira bugs by assignment group",
    "Create a pie chart of resolution types this week",
    "List tickets reopened more than once",
    "What changed in defect count vs last week?",
    "Give me the top 5 root causes this month",
]

# Layout
col1, col2 = st.columns([1, 3], gap="large")

with col1:
    with st.container(border=True):
        st.subheader("⚡ Quick Suggestions")
        for idx, text in enumerate(SUGGESTIONS):
            if st.button(text, key=f"sugg_{idx}", use_container_width=True):
                st.session_state.chat_draft = text
                st.rerun()

with col2:
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_draft" not in st.session_state:
        st.session_state.chat_draft = ""

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_msg = st.chat_input("Type your message…", key="chat_draft")
    if user_msg:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        # Add assistant response
        response = f"✅ Got it! Processing: {user_msg}"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
