import streamlit as st
from paper_ticher import PaperTicher

paper_ticher = PaperTicher()
llm = paper_ticher.get_llm_model()

# RTL CSS styling
rtl_css = """
<style>
    .rtl {
        direction: rtl;
        text-align: right;
        font-family: 'Arial', sans-serif;
    }
    .user-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        float: right;
    }
    .bot-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        float: right;
    }
    .stTextInput>div>div>input {
        direction: rtl;
        text-align: right;
    }
</style>
"""
st.markdown(rtl_css, unsafe_allow_html=True)

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.header("Paper Ticher Chatbot")


# Sidebar for HTML upload
with st.sidebar:
    st.header("File Upload")
    uploaded_file = st.file_uploader("Upload Papre file", type=[".pdf"])
    paper_ticher.set_paper_path(uploaded_file)
    file_content = paper_ticher.get_paper_content()
    if st.session_state.messages == [] and file_content is not None:
        with st.spinner("Preparing the paper abstract"):
            st.write(paper_ticher.get_paper_structure())

        

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Apply RTL styling with message-specific formatting
        div_class = "user-message" if msg["role"] == "user" else "bot-message"
        st.markdown(
            f'<div class="{div_class} rtl">{msg["content"]}</div>', 
            unsafe_allow_html=True
        )

# User input handling
prompt = st.chat_input("Type your message here...")
if prompt:
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(
            f'<div class="user-message rtl">{prompt}</div>', 
            unsafe_allow_html=True
        )

    # Generate bot response (example implementation)
    st.session_state.messages.append({"role": "user", "content": file_content})
    answer = paper_ticher.llm_response(st.session_state.messages)
    st.session_state.messages.pop()  
    # Store and display bot response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(
            f'<div class="bot-message rtl">{answer}</div>', 
            unsafe_allow_html=True
        )