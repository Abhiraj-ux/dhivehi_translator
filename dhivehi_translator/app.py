import streamlit as st
import os
from scraper import scrape_website, get_random_wikipedia_article, is_dhivehi_text
from translator import translate_content, translate_text
import streamlit.components.v1 as components
import time
import PyPDF2
import docx
import io
import base64

# Custom CSS for a more professional look
def apply_custom_css():
    st.markdown("""
    <style>
    .main-header {color: #1E3A8A; font-family: 'Segoe UI', sans-serif; font-weight: 600;}
    .tab-subheader {color: #2563EB; font-family: 'Segoe UI', sans-serif; font-weight: 500; font-size: 1.2rem;}
    .info-text {color: #4B5563; font-family: 'Segoe UI', sans-serif;}
    .stButton>button {background-color: #2563EB; color: white; border-radius: 4px; border: none; padding: 0.5rem 1rem;}
    .stButton>button:hover {background-color: #1E40AF;}
    .stProgress .st-bo {background-color: #3B82F6;}
    .success-box {background-color: #DCFCE7; padding: 1rem; border-radius: 4px; border-left: 4px solid #22C55E;}
    .warning-box {background-color: #FEF9C3; padding: 1rem; border-radius: 4px; border-left: 4px solid #EAB308;}
    .error-box {background-color: #FEE2E2; padding: 1rem; border-radius: 4px; border-left: 4px solid #EF4444;}
    .file-uploader {border: 2px dashed #3B82F6; border-radius: 8px; padding: 20px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file"""
    try:
        doc = docx.Document(docx_file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def extract_text_from_txt(txt_file):
    """Extract text from a TXT file"""
    try:
        text = txt_file.getvalue().decode("utf-8")
        return text
    except Exception as e:
        return f"Error extracting text from TXT: {str(e)}"

def create_download_link(content, filename, link_text):
    """Create a download link for text content"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def main():
    st.set_page_config(page_title="Dhivehi-English Translator", page_icon="🌐", layout="wide")
    apply_custom_css()
    
    # Set Google Cloud credentials
    credentials_path = "c:\\Users\\Lenovo\\dhivehi_translator\\first-presence-450616-g0-a3ffbe9e307e.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    
    st.markdown("<h1 class='main-header'>Dhivehi-English Translator</h1>", unsafe_allow_html=True)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Website Translation", "Direct Text", "File Translation", "Dhivehi Language"])
    
    with tab1:
        st.markdown("<h3 class='tab-subheader'>Website Translation</h3>", unsafe_allow_html=True)
        
        # Input options in a cleaner layout
        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input("Enter website URL:", "https://dhivehiacademy.edu.mv/thasavvaru")
        with col2:
            if st.button("Random Wikipedia"):
                with st.spinner("Getting article..."):
                    url = get_random_wikipedia_article()
                    st.session_state.url = url
                    st.info(f"URL: {url}")
        
        # Language selection in a cleaner layout
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            source_lang = st.selectbox(
                "From:",
                [("Auto-detect", "auto"), ("Dhivehi", "dv"), ("English", "en")],
                format_func=lambda x: x[0]
            )[1]
        
        with col2:
            target_lang = st.selectbox(
                "To:",
                [("English", "en"), ("Dhivehi", "dv"), ("Arabic", "ar"), ("Hindi", "hi"), ("Urdu", "ur")],
                format_func=lambda x: x[0]
            )[1]
        
        with col3:
            timeout = st.slider("Timeout:", min_value=5, max_value=30, value=15)
        
        # Scrape and translate button
        if st.button("Translate Website"):
            progress_bar = st.progress(0)
            status = st.empty()
            
            # Step 1: Scraping
            status.text("Scraping website...")
            progress_bar.progress(10)
            content = scrape_website(url, timeout=timeout)
            progress_bar.progress(40)
            
            if 'error' in content:
                st.error(f"Error: {content['error']}")
                progress_bar.empty()
                status.empty()
            else:
                # Step 2: Language detection
                status.text("Detecting language...")
                progress_bar.progress(50)
                
                if source_lang == 'auto':
                    if (content['title'] and is_dhivehi_text(content['title'])) or \
                       (content['paragraphs'] and is_dhivehi_text(content['paragraphs'][0])):
                        source_lang = 'dv'
                        st.info("Detected Dhivehi content")
                    else:
                        source_lang = 'en'
                        st.info("Detected English content")
                
                # Step 3: Translation
                status.text("Translating...")
                progress_bar.progress(60)
                translated_content = translate_content(content, source_lang, target_lang)
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()
                status.empty()
                
                st.success("Translation complete!")
                
                # Display the translated content
                st.subheader("Title")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Original:")
                    st.write(translated_content['original_title'])
                with col2:
                    st.write("Translated:")
                    st.write(translated_content['translated_title'])
                
                # Display content in expandable sections
                with st.expander("View Translated Content", expanded=True):
                    for i, para in enumerate(translated_content['paragraphs']):
                        st.markdown(f"**Paragraph {i+1}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("Original:")
                            st.write(para['original'])
                        with col2:
                            st.write("Translated:")
                            st.write(para['translated'])
                        st.markdown("---")
    
    with tab2:
        st.markdown("<h3 class='tab-subheader'>Direct Text Translation</h3>", unsafe_allow_html=True)
        
        # Language selection in a cleaner layout
        col1, col2 = st.columns(2)
        with col1:
            direct_source_lang = st.selectbox(
                "From:",
                [("Auto-detect", "auto"), ("English", "en"), ("Dhivehi", "dv")],
                format_func=lambda x: x[0],
                key="direct_source"
            )[1]
        
        with col2:
            target_options = [("English", "en"), ("Dhivehi", "dv")]
            if direct_source_lang != 'auto':
                target_options = [opt for opt in target_options if opt[1] != direct_source_lang]
            
            direct_target_lang = st.selectbox(
                "To:",
                target_options,
                format_func=lambda x: x[0],
                key="direct_target"
            )[1]
        
        # Text input for translation
        input_text = st.text_area("Enter text to translate:", height=150)
        
        if st.button("Translate Text"):
            if input_text:
                if direct_source_lang == 'auto':
                    if is_dhivehi_text(input_text):
                        direct_source_lang = 'dv'
                        st.info("Detected Dhivehi text")
                    else:
                        direct_source_lang = 'en'
                        st.info("Detected English text")
                
                with st.spinner("Translating..."):
                    translated_text = translate_text(input_text, direct_source_lang, direct_target_lang)
                
                st.success("Translation complete!")
                st.subheader("Translation Result:")
                st.write(translated_text)
            else:
                st.warning("Please enter some text to translate.")
    
    with tab3:
        st.markdown("<h3 class='tab-subheader'>File Translation</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        Upload PDF, DOCX, or TXT files to extract and translate their content.
        """)
        
        # File uploader
        st.markdown("<div class='file-uploader'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Language selection
        col1, col2 = st.columns(2)
        with col1:
            file_source_lang = st.selectbox(
                "From:",
                [("Auto-detect", "auto"), ("English", "en"), ("Dhivehi", "dv")],
                format_func=lambda x: x[0],
                key="file_source"
            )[1]
        
        with col2:
            file_target_lang = st.selectbox(
                "To:",
                [("English", "en"), ("Dhivehi", "dv"), ("Arabic", "ar"), ("Hindi", "hi"), ("Urdu", "ur")],
                format_func=lambda x: x[0],
                key="file_target"
            )[1]
        
        if uploaded_file is not None:
            # Display file info
            file_details = {"Filename": uploaded_file.name, "File size": f"{uploaded_file.size / 1024:.2f} KB"}
            st.write("File Details:")
            for key, value in file_details.items():
                st.write(f"- {key}: {value}")
            
            # Extract text based on file type
            if st.button("Extract and Translate"):
                with st.spinner("Processing file..."):
                    # Extract text based on file type
                    if uploaded_file.name.endswith('.pdf'):
                        extracted_text = extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.name.endswith('.docx'):
                        extracted_text = extract_text_from_docx(uploaded_file)
                    elif uploaded_file.name.endswith('.txt'):
                        extracted_text = extract_text_from_txt(uploaded_file)
                    else:
                        extracted_text = "Unsupported file format"
                
                if "Error" in extracted_text:
                    st.error(extracted_text)
                else:
                    st.success("Text extracted successfully!")
                    
                    # Display extracted text in an expander
                    with st.expander("View Extracted Text", expanded=False):
                        st.write(extracted_text)
                    
                    # Auto-detect language if needed
                    if file_source_lang == 'auto':
                        if is_dhivehi_text(extracted_text):
                            file_source_lang = 'dv'
                            st.info("Detected Dhivehi text")
                        else:
                            file_source_lang = 'en'
                            st.info("Detected English text")
                    
                    # Translate the extracted text
                    with st.spinner("Translating..."):
                        translated_text = translate_text(extracted_text, file_source_lang, file_target_lang)
                    
                    st.success("Translation complete!")
                    
                    # Display translation in columns
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Original Text (Preview)")
                        st.write(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                    
                    with col2:
                        st.subheader("Translated Text (Preview)")
                        st.write(translated_text[:500] + "..." if len(translated_text) > 500 else translated_text)
                    
                    # Full translation in expander
                    with st.expander("View Full Translation", expanded=True):
                        st.write(translated_text)
                    
                    # Download options
                    st.markdown("### Download Options")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            "Download Original Text",
                            extracted_text,
                            file_name=f"original_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain"
                        )
                    
                    with col2:
                        st.download_button(
                            "Download Translation",
                            translated_text,
                            file_name=f"translated_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain"
                        )
    
    with tab4:
        st.markdown("<h3 class='tab-subheader'>About Dhivehi Language</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        ## Dhivehi Language History and Overview
        
        **Dhivehi** (ދިވެހި), also known as **Maldivian**, is an Indo-Aryan language predominantly spoken in the Maldives and in Minicoy Island in the Union Territory of Lakshadweep, India, where it is known as **Mahl**. It is the official language of the Maldives and one of the oldest living languages in the Indo-Aryan family.
        
        ### Origins and Classification
        
        Dhivehi is descended from the Prakrit language of ancient India and shows significant influence from Pali, the liturgical language of Theravada Buddhism. It belongs to the Indo-Aryan branch of the Indo-European language family and is closely related to Sinhala (spoken in Sri Lanka). The language evolved in relative isolation, which has helped preserve many archaic features.
        
        ### Historical Development
        
        The historical development of Dhivehi can be divided into several periods:
        
        1. **Early Prakrit Period (before 500 CE)**: The earliest form of Dhivehi developed from Prakrit languages brought by settlers from northern India.
        
        2. **Transitional Period (500-1100 CE)**: During this period, Dhivehi began to develop distinct characteristics from other Indo-Aryan languages, influenced by the geographical isolation of the Maldives.
        
        3. **Medieval Period (1100-1700 CE)**: This period saw the introduction of Arabic influence following the conversion of the Maldives to Islam in 1153 CE. Many Arabic loanwords entered the language during this time.
        
        4. **Modern Period (1700 CE-present)**: The modern form of Dhivehi has been influenced by colonial contacts with Portuguese, Dutch, and English, as well as more recent influences from global communication.
        
        ### Writing System
        
        Dhivehi has used several writing systems throughout its history:
        
        1. **Eveyla Akuru**: An ancient script derived from Brahmi, used until the 13th century.
        
        2. **Dhives Akuru**: A script that evolved from Eveyla Akuru, used from the 13th to the 18th centuries.
        
        3. **Thaana**: The current script, developed in the 18th century. Unlike the previous scripts which were written from left to right, Thaana is written from right to left. It was originally used to write secret magical formulas, with characters derived from Arabic numerals, Arabic letters, and indigenous number symbols.
        
        The Thaana alphabet consists of 24 letters with vowel signs called fili. The unique aspect of Thaana is that it was specifically created for the Dhivehi language, unlike many other scripts that evolved naturally over time.
        
        ### Dialects
        
        Dhivehi has several dialects, with variations primarily based on geography:
        
        1. **Standard Dhivehi**: Spoken in Malé, the capital, and used in education and media.
        
        2. **Southern Dialects**: Spoken in the southern atolls, with distinctive vocabulary and pronunciation.
        
        3. **Addu Dialect**: Spoken in Addu Atoll, the southernmost atoll of the Maldives.
        
        4. **Huvadhu Dialect**: Spoken in Huvadhu Atoll.
        
        5. **Mulaku Dialect**: Spoken in Mulaku Atoll.
        
        6. **Mahl**: The dialect spoken in Minicoy Island, India, which has been influenced by Malayalam.
        
        ### Vocabulary and Grammar
        
        Dhivehi vocabulary is primarily derived from Sanskrit and Pali, with significant borrowings from Arabic, particularly for religious, administrative, and commercial terms. More recent loanwords come from Portuguese, Dutch, English, and Hindi.
        
        The grammar of Dhivehi is characterized by:
        
        - Subject-Object-Verb (SOV) word order
        - Postpositions rather than prepositions
        - A complex system of honorifics reflecting social status
        - No grammatical gender
        - Agglutinative morphology, where words are formed by joining morphemes together
        
        ### Current Status
        
        Dhivehi is spoken by approximately 350,000 people worldwide. As the official language of the Maldives, it is used in government, education, and media. The language faces challenges from the increasing use of English in education, tourism, and international communication, but efforts are being made to preserve and promote it through language policies and cultural initiatives.
        
        The Dhivehi language is a vital part of Maldivian cultural identity and continues to evolve while maintaining its unique characteristics.
        """)
        
        # Add a section for learning resources
        st.markdown("---")
        st.markdown("### Learning Resources")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dhivehi Dictionary**")
            st.markdown("Official Dhivehi-English Dictionary")
            if st.button("Open Dictionary", key="dict_btn"):
                js = """<script>window.open("https://www.radheef.mv/", "_blank")</script>"""
                st.components.v1.html(js, height=0)
                
            st.markdown("**Dhivehi Language Academy**")
            st.markdown("Official language authority of Maldives")
            if st.button("Open Academy Website", key="acad_btn"):
                js = """<script>window.open("https://dhivehiacademy.edu.mv/", "_blank")</script>"""
                st.components.v1.html(js, height=0)
        
        with col2:
            st.markdown("**Dhivehi Wikipedia**")
            st.markdown("Wikipedia in Dhivehi language")
            if st.button("Open Dhivehi Wikipedia", key="wiki_btn"):
                js = """<script>window.open("https://dv.wikipedia.org/", "_blank")</script>"""
                st.components.v1.html(js, height=0)
                
            st.markdown("**Learn Dhivehi Online**")
            st.markdown("Free online Dhivehi language courses")
            if st.button("Open Learning Resources", key="learn_btn"):
                js = """<script>window.open("https://www.101languages.net/dhivehi/", "_blank")</script>"""
                st.components.v1.html(js, height=0)

if __name__ == "__main__":
    main()