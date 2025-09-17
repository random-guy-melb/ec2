layout = """
layout = """
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f0f0f0 0%, #f2f2f2 10%, #f5f5f5 20%, #f8f8f8 40%, #fff8f2 60%, #fff0eb 80%, #ffe8e0 100%);
}

/* Ensure the wrapper doesn't override our transparency */
[data-testid="stVerticalBlockBorderWrapper"][height="350"] {
    background: white !important;
}

/* Hide Streamlit header elements */
header[data-testid="stHeader"],
.stApp > header {
    display: none !important;
}

.main > div:first-child {
    padding-top: 1rem !important;
    background: transparent !important;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 0rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-width: 3px;
    border-radius: 8px !important;
    border-color: black;
}

[data-testid="stContainer"] {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
}

/* Chat input specific styling - UPDATED */
.stChatInput {
    position: relative !important;
    bottom: auto !important;
    width: 100% !important;
    margin: 0 !important;
}

.stChatInput,
.stChatInput *,
.stChatInput > div {
    border-color: transparent !important;
    outline: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* Set consistent height for chat_input */
.stChatInput textarea {
    height: 40px !important;
    min-height: 40px !important;
    max-height: 40px !important;
    padding: 8px 12px !important;
    resize: none !important;
    overflow: hidden !important;
    border: 1px solid rgb(228, 231, 237) !important;
    border-radius: 8px !important;
}

.stChatInput > div:focus-within {
    background: white;
    border-color: transparent !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Audio input styling */
.stAudioInput {
    margin: 0 !important;
}

.stAudioInput,
.stAudioInput > div,
.stAudioInput > div > div,
[data-testid="stAudioInput"] {
    height: 40px !important;
    max-height: 40px !important;
}

/* Align columns for inputs */
[data-testid="column"] > div {
    display: flex;
    align-items: center;
    height: 100%;
}

/* Override the default chat input styling */
div[data-testid="stChatInput"] {
    position: relative !important;
    width: 100% !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* General input styling */
input {
    font-size: 1rem !important;
    border-radius: 6px !important;
    padding: 0.7rem !important;
}

input:focus,
input:hover,
input:active,
input *,
.stTextInput > div,
[data-baseweb="input"],
[data-baseweb="input"] * {
    border-color: transparent !important;
    outline: none !important;
    box-shadow: none !important;
}

[data-testid="stSidebarNavLink"] {
    display: none;
}

/* Hide avatars */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}

/* Button styling */
button[data-testid="stBaseButton-secondary"] {
    background-color: black;
    color: white;
    border: 2px solid black !important;
}

button[data-testid="stBaseButton-secondary"]:active,
button[data-testid="stBaseButton-secondary"]:active div {
    background-color: black;
    color: white !important;
    transform: scale(1.0);
    transition: transform 0.1s ease, box-shadow 0.1s ease;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

button[data-testid="stBaseButton-secondary"]:hover {
    color: white;
    transform: scale(1.0);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

button[data-testid="stBaseButton-secondary"]:focus {
    color: white;
    outline: 2px solid #666666;
    outline-offset: 2px;
    transform: scale(1.0);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

button[data-testid="stBaseButton-primary"] {
    background-color: black;
    color: white;
    border: 2px solid black !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

button[data-testid="stBaseButton-primary"]:hover {
    transform: scale(1.0);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* ========== FIXED USER MESSAGE STYLING ========== */

/* Container for user messages - right aligned */
.stChatMessage:has([data-testid="stChatMessageAvatarUser"]) {
    display: flex !important;
    justify-content: flex-end !important;
    width: 100% !important;
    margin: 8px 0 !important;
    padding: 0 !important;
    background: transparent !important;
}

/* User message bubble - fits content */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, #E8605C 0%, #F9B3A4 100%) !important;
    color: black !important;
    border-radius: 18px !important;
    padding: 10px 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    word-wrap: break-word !important;
    white-space: pre-wrap !important;
}

/* User message content wrapper */
[data-testid="stChatMessageContent"]:has(+ [data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessageAvatarUser"] + [data-testid="stChatMessageContent"] {
    display: inline-block !important;
    width: auto !important;
    max-width: 100% !important;
    background: transparent !important;
}

/* User message text content */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    display: inline !important;
}

/* ========== ASSISTANT MESSAGE STYLING ========== */

/* Assistant message container */
.stChatMessage:has([data-testid="stChatMessageAvatarAssistant"]) {
    display: flex !important;
    justify-content: flex-start !important;
    width: 100% !important;
    margin: 8px 0 !important;
    padding: 0 !important;
    background: transparent !important;
}

/* Assistant message bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: white !important;
    border-radius: 18px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    padding: 12px 16px !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    min-height: 40px !important;
    color: rgb(45, 55, 72) !important;
    font-weight: 500 !important;
    text-rendering: optimizeLegibility !important;
    -webkit-font-smoothing: antialiased !important;
}

/* Assistant message content */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}

/* Ensure all message children have transparent backgrounds */
[data-testid="stChatMessage"] > * {
    background: transparent !important;
}

/* Remove any default Streamlit message styling that might interfere */
.stChatMessage {
    flex-direction: row !important;
}

/* Fix for message content container */
[data-testid="stChatMessageContent"] {
    width: auto !important;
    flex-grow: 0 !important;
    display: inline-block !important;
}
"""
"""
