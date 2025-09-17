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
    padding:10 px;
}

.chat-message.user {
    flex-direction: row-reverse;
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

/* Set consistent height for chat_input - NEW */
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

/* Audio input styling - NEW */
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

/* Align columns for inputs - NEW */
[data-testid="column"] > div {
    display: flex;
    align-items: center;
    height: 100%;
}

/* Create a flex container for the inputs - NEW */
.chat-audio-container {
    display: flex !important;
    gap: 10px !important;
    align-items: center !important;
    padding: 10px 0 !important;
}

/* Adjust chat_input container width - NEW */
.chat-audio-container > div:first-child {
    flex: 3 !important;
}

/* Adjust audio_input container width - NEW */
.chat-audio-container > div:last-child {
    flex: 1 !important;
}

/* Override the default chat input styling - NEW */
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

[data-testid="stChatMessageAvatarUser"] {
    display: none;
}

div[data-testid="stChatMessageContent"] > div[aria-label="Chat message from user"] {
    background-color: #DC4C2C !important;
}

[data-testid="stChatMessageAvatarAssistant"] {
    display: none;
}

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

/* Hide user and bot avatars (optional) */
/* Hide user avatar (optional) */
/* Hide the assistant avatar */
[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}

/* User message container styling */
.stChatMessage:has([data-testid="stChatMessageAvatarUser"]) {
    display: inline-flex;
    align-items: center;
    margin-left: auto;
    margin-right: 1rem;
    max-width: 70%;
    vertical-align: top;
}

/* User message bubble styling */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, rgba(0, 82, 204, 0.6) 0%, rgba(38, 132, 255, 0.45) 100%);
    color: black;
    border-radius: 10px;
    padding: 12px 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    min-height: 50px;
}

/* Assistant message container and content styling */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: white;
    border-radius: 10px;
    box-shadow: 0 .1px 3px rgba(0, 0, 0.01);
    margin: 8px 0;
    padding: 12px 16px;
    width: 100%;
    min-height: 50px;
    color: rgb(45, 55, 72);
    font-weight: bold;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
}

/* Style for the empty container during animation */
.element-container:has([data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])) {
    background: #f7f7f8;
    border-radius: 10px;
    margin: 8px 0;
    min-height: 50px;
    width: 100%;
}

/* Text alignment and transparent backgrounds */
[data-testid="stChatMessageAvatarUser"] + [data-testid="stChatMessageContent"] {
    text-align: left !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > * {
    background: transparent !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) > * {
    background: transparent !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > * {
    background: transparent !important;
}

/* Right-align user messages */
.stChatMessage:has([data-testid="stChatMessageAvatarUser"]) {
    display: flex;
    flex-direction: row-reverse;
    align-items: end;
}

[data-testid="stChatMessageAvatarUser"] + [data-testid="stChatMessageContent"] {
    text-align: right;
}

/* Style only user messages */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, #E8605C 0%, #F9B3A4 100%);
    color: black;
    border-radius: 10px;
    padding: 12px 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    min-height: 60px;
}

[data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}
"""
