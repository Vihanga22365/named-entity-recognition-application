import os
import streamlit as st
import fitz
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import pdfplumber
from PIL import Image
from PIL import Image
from io import BytesIO
import base64

load_dotenv()

os.environ["GOOGLE_API_KEY"]=os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-exp-1206",
    temperature=0,
)

st.set_page_config(layout="wide")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

def get_entities(entity_name, additional_context, text):
    system = """You are a specialization for recognize entities from the given 'Document Context'.  when user give the 'Entity Name' and the 'Additional Instruction Given For Identify Entity', according to the 'Document Context' you have to identify the entity value from the given 'Document Context'. Identify entity value only. nothing else."""
    human = f"""
        Entity Name: {entity_name}
        Additional Instruction Given For Identify Entity: {additional_context}
        Document Context: {text}
    """
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    chain = prompt | llm
    text = "What is the capital of France?"
    
    answer = chain.invoke({})
    
    return answer.content

if uploaded_file is not None:
    # Read the PDF file
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()

    # Display the extracted text
    # st.text_area("Extracted Text", text, height=300)
    
    # Display PDF preview with navigation buttons
    with pdfplumber.open(uploaded_file) as pdf:
        num_pages = len(pdf.pages)
        
        # Initialize session state for current page
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        
        custom_page = st.number_input("Go to page", min_value=1, max_value=num_pages, value=st.session_state.current_page)
        if custom_page != st.session_state.current_page:
            st.session_state.current_page = custom_page
        
        # Center the page number display
        st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page} of {num_pages}</div>", unsafe_allow_html=True)


        # Display the selected page
        page = pdf.pages[st.session_state.current_page - 1]
        page_image = page.to_image(resolution=600)  # Increase resolution
        image_path = f"page_{st.session_state.current_page}.png"
        page_image.save(image_path)
        img_buffer = BytesIO()
        page_image.save(img_buffer, format="PNG")
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center;'>
                <img src='data:image/png;base64,{img_str}' alt='Preview of page {st.session_state.current_page} of the PDF' width='700'/>
            </div>
            """,
            unsafe_allow_html=True
        )


    # Initialize session state for entities
    if 'entities' not in st.session_state:
        st.session_state.entities = []

    # Form to add entity and additional context
    with st.form(key='entity_form'):
        entity_name = st.text_input("Entity Name")
        additional_context = st.text_area("Additional Context", height=100)
        submit_button = st.form_submit_button(label='Add Entity')

        if submit_button:
            if entity_name:
                
                entity_value = get_entities(entity_name, additional_context, text)
                
                st.session_state.entities.append({
                    "Entity Name": entity_name,
                    "Additional Context": additional_context,
                    "Entity Value": entity_value
                })
            else:
                st.error("Entity Name is required")

    # Display the table of entities
    if st.session_state.entities:
        st.table(st.session_state.entities)


