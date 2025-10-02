/* 1) Right-align the row that has the USER avatar */
div[class*="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  display: flex;                 /* ensure it's a flex row */
  justify-content: flex-end;     /* push content to the right */
}

/* 2) Shrink-wrap the content block (sibling of avatar) */
div[class*="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > :not([data-testid^="stChatMessageAvatar"]) {
  margin-left: auto;             /* right side */
  display: inline-flex;          /* shrink to content */
  flex: 0 0 auto;                /* don't stretch */
  width: fit-content;            /* shrink */
  max-width: min(75%, 820px);    /* wrap long text / code */
  align-self: flex-end;          /* align bubble bottom with row */
}

/* 3) Prevent inner content from forcing full width */
div[class*="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"],
div[class*="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) pre {
  width: fit-content;
  max-width: 100%;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}
