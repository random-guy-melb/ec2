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

/* Chat input specific styling */
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

/* Reset default chat message styling first */
.stChatMessage {
    background: transparent !important;
    padding: 0 !important;
}

/* User message - main container */
.stChatMessage[data-testid="stChatMessageContainer-user"] {
    display: flex !important;
    justify-content: flex-end !important;
    width: 100% !important;
    margin: 8px 0 !important;
}

/* User message bubble - content wrapper */
.stChatMessage[data-testid="stChatMessageContainer-user"] > div:first-child {
    background: linear-gradient(135deg, #E8605C 0%, #F9B3A4 100%) !important;
    color: black !important;
    border-radius: 18px !important;
    padding: 10px 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    margin-left: auto !important;
    word-wrap: break-word !important;
    white-space: pre-wrap !important;
}

/* Alternative selectors for user messages in case structure varies */
[data-testid="stChatMessage"]:has(.stChatMessageContent[data-testid*="user"]),
[data-testid="stChatMessage"]:has([aria-label*="user" i]) {
    display: flex !important;
    justify-content: flex-end !important;
    width: 100% !important;
    background: transparent !important;
}

[data-testid="stChatMessage"]:has(.stChatMessageContent[data-testid*="user"]) > div,
[data-testid="stChatMessage"]:has([aria-label*="user" i]) > div {
    background: linear-gradient(135deg, #E8605C 0%, #F9B3A4 100%) !important;
    color: black !important;
    border-radius: 18px !important;
    padding: 10px 16px !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    margin-left: auto !important;
}

/* User message text content */
.stChatMessage[data-testid="stChatMessageContainer-user"] p,
.stChatMessage[data-testid="stChatMessageContainer-user"] div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    color: black !important;
}

/* ========== ASSISTANT MESSAGE STYLING ========== */

/* Assistant message - main container */
.stChatMessage[data-testid="stChatMessageContainer-assistant"] {
    display: flex !important;
    justify-content: flex-start !important;
    width: 100% !important;
    margin: 8px 0 !important;
}

/* Assistant message bubble */
.stChatMessage[data-testid="stChatMessageContainer-assistant"] > div:first-child {
    background: white !important;
    border-radius: 18px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    padding: 12px 16px !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    margin-right: auto !important;
    min-height: 40px !important;
    color: rgb(45, 55, 72) !important;
    font-weight: 500 !important;
    text-rendering: optimizeLegibility !important;
    -webkit-font-smoothing: antialiased !important;
}

/* Alternative selectors for assistant messages */
[data-testid="stChatMessage"]:has(.stChatMessageContent[data-testid*="assistant"]),
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) {
    display: flex !important;
    justify-content: flex-start !important;
    width: 100% !important;
    background: transparent !important;
}

[data-testid="stChatMessage"]:has(.stChatMessageContent[data-testid*="assistant"]) > div,
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) > div {
    background: white !important;
    border-radius: 18px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    padding: 12px 16px !important;
    display: inline-block !important;
    max-width: 70% !important;
    width: auto !important;
    margin-right: auto !important;
}

/* Assistant message text content */
.stChatMessage[data-testid="stChatMessageContainer-assistant"] p,
.stChatMessage[data-testid="stChatMessageContainer-assistant"] div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}

/* Remove any default padding/margins that might interfere */
[data-testid="stChatMessageContent"] {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

/* Ensure proper text wrapping in all messages */
.stChatMessage p {
    word-wrap: break-word !important;
    white-space: pre-wrap !important;
    overflow-wrap: break-word !important;
}

/* Fix for any potential flexbox issues */
.stChatMessage > div {
    flex-shrink: 0 !important;
}

/* Override any default Streamlit chat message backgrounds */
div[class*="ChatMessage"] {
    background: transparent !important;
}
"""
