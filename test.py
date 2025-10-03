st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}

    .custom-banner {
        background: linear-gradient(135deg, #5DD9C1 0%, #00A982 100%);
        padding: 20px;
        border-radius: 0 0 15px 15px;
        margin: 0 -70px 30px -70px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .banner-title {
        color: white;
        font-size: 32px;
        font-weight: 500;
        text-align: center;
        letter-spacing: 2px;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }

    .main {
        background-color: #F0FDF9;
    }

    .stChatInputContainer textarea {
        border-radius: 24px !important;
        border: 2px solid #E5E7EB !important;
        background-color: #FAFAFA !important;
        color: #1F2937 !important;
    }

    .stChatInputContainer textarea:focus {
        border-color: #5DD9C1 !important;
        box-shadow: 0 0 0 3px rgba(93, 217, 193, 0.1) !important;
    }

    /* Style suggestions container */
    .st-key-sugg_container {
        border: 3px solid #5DD9C1 !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }

    /* Style suggestions heading */
    .st-key-sugg_container h3 {
        font-size: 16px !important;
        color: #00A982 !important;
    }

    /* Target suggestion buttons using the container class with sugg_ */
    [class*="sugg_"] button {
        background-color: #E6F9F5 !important;
        color: #00755C !important;
        border-radius: 20px !important;
        border: 1px solid #5DD9C1 !important;
        font-weight: 500 !important;
    }

    [class*="sugg_"] button:hover {
        background-color: #C7F2E9 !important;
        border-color: #00A982 !important;
    }

    /* Target the text div inside suggestion buttons */
    [class*="sugg_"] button div {
        font-size: 13px !important;
    }
    </style>
    """, unsafe_allow_html=True)
