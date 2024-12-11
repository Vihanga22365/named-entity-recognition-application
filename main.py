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
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

    html, body, div, span, h1, h2, h3, h4, h5, app-view-root, [class*="css"]  {
        font-family: 'Poppins', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)


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

    # Initialize session state for entities
    if 'entities' not in st.session_state:
        st.session_state.entities = []

    if 'num_columns' not in st.session_state:
        st.session_state.num_columns = 2

    def add_column():
        st.session_state.num_columns += 1

    # Determine the number of rows needed
    num_rows = (st.session_state.num_columns + 1) // 2

    for row in range(num_rows):
        columns = st.columns(2)
        for i in range(2):
            col_index = row * 2 + i
            if col_index < st.session_state.num_columns:
                with columns[i]:
                    
                    with st.form(key=f'entity_form_{col_index}'):
                        st.markdown(f"#### Name Entity {col_index + 1}")
                        entity_name = st.text_input("Entity Name", key=f'entity_name_{col_index}')
                        additional_context = st.text_area("Additional Context", height=100, key=f'additional_context_{col_index}')
                        submit_button = st.form_submit_button(label='Add Entity')

                        if submit_button:
                            if entity_name:
                                # Check if the entity is already in the session state
                                if not any(entity["Entity Name"] == entity_name and entity["Additional Context"] == additional_context for entity in st.session_state.entities):
                                    entity_value = get_entities(entity_name, additional_context, text)
                                    st.session_state.entities.append({
                                        "Entity Name": entity_name,
                                        "Additional Context": additional_context,
                                        "Entity Value": entity_value
                                    })
                                    st.markdown(f"##### Entity Value: {entity_value}")
                                    # Check if all current columns have entity values
                                    if all(f'entity_name_{j}' in st.session_state and st.session_state[f'entity_name_{j}'] for j in range(st.session_state.num_columns)):
                                        add_column()
                                    st.rerun()
                            else:
                                st.error("Entity Name is required")

                        # Display all entity values for the current column
                        previous_entity_value = None

                        for entity in st.session_state.entities:
                            if entity["Entity Name"] == st.session_state.get(f'entity_name_{col_index}'):
                                current_entity_value = entity['Entity Value']
                                if current_entity_value != previous_entity_value:
                                    st.markdown(f"##### Entity Value: {current_entity_value}")
                                    previous_entity_value = current_entity_value
                                break  # Exit the loop after finding the first matching entity


