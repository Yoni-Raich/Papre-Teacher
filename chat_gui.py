import streamlit as st
from paper_teacher import PaperTicher

paper_teacher = PaperTicher()
llm = paper_teacher.get_llm_model()

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
    st.header("Paper teacher Chatbot")

llm_name = None
llm_name = st.selectbox("select llm model",["gemini-2.0-flash-thinking-exp-01-21","learnlm-1.5-pro-experimental", "gemini-2.0-flash-exp", "azure"])
if llm_name:
    paper_teacher.set_llm_model(llm_name)
    llm_name = None
    
sections_list = []
with st.sidebar:
    st.header("File Upload")
    uploaded_file = st.file_uploader("Upload Paper file", type=[".pdf"])
    
    if uploaded_file:
        # Reset processing flag if new file uploaded
        if 'processed_file' not in st.session_state or st.session_state.processed_file != uploaded_file.name:
            st.session_state.processed_file = uploaded_file.name
            st.session_state.sections_processed = False  # Reset processing flag
        
        paper_teacher.set_paper_path(uploaded_file)
        file_content = paper_teacher.get_paper_content()

        # Process sections only once per file
        if file_content and not st.session_state.get('sections_processed', False):
            with st.spinner("Preparing paper abstract"):
                sections = paper_teacher.get_paper_section()
                st.session_state.sections = sections
                st.session_state.sections_processed = True

        # Create buttons using cached sections
        if st.session_state.get('sections_processed', False):
            for section, subsections in st.session_state.sections['sections'].items():
                with st.expander(section):
                    if subsections == []:
                        subsections.append(section)
                    for sub in subsections:
                        if st.button(sub):
                            st.session_state.subsection_clicked = True
                            st.session_state.messages = []
                            st.session_state.selected_subsection = sub
                            sections_list.append(sub)

# Handle button clicks
if st.session_state.get('subsection_clicked', False):
    st.session_state.subsection_clicked = False
    section_content = paper_teacher.get_section_content(st.session_state.selected_subsection, sections_list)
    auto_prompt = f" בבקשה תסביר את הסקשן ובעברית : {section_content}"

    # Add auto-generated message to chat
    st.session_state.messages.append({"role": "user", "content": auto_prompt})
    
    # Generate and display response
    with st.spinner("Generating explanation..."):
        st.session_state.messages.append({"role": "user", "content": file_content})
        answer = paper_teacher.llm_response(st.session_state.messages)
        st.session_state.messages.pop()
        st.session_state.messages.pop()  # Remove auto-generated message
        st.session_state.messages.append({"role": "assistant", "content": answer})  

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
    answer = paper_teacher.llm_response(st.session_state.messages)
    st.session_state.messages.pop()  
    # Store and display bot response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(
            f'<div class="bot-message rtl">{answer}</div>', 
            unsafe_allow_html=True
        )