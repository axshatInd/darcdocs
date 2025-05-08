import streamlit as st

def setup_page_config():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="DarcDocs - PDF Dark Mode Converter",
        page_icon="🌙",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "# DarcDocs\nConvert your PDFs to dark mode for comfortable reading."
        }
    )

def apply_custom_css():
    """Apply custom CSS for dark mode UI."""
    st.markdown("""
    <style>
        .main {
            background-color: #121212;
            color: #FFFFFF;
        }
        .stButton>button {
            background-color: #BB86FC;
            color: #000000;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #9966CC;
        }
        /* Removed the upload-area class styling */
        .success-message {
            background-color: #03DAC5;
            color: #000000;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .error-message {
            background-color: #CF6679;
            color: #000000;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .stProgress > div > div > div {
            background-color: #BB86FC;
        }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create the sidebar with customization options."""
    with st.sidebar:
        st.header("Customization Options")
        bg_color = st.color_picker("Background Color", "#000000")
        text_color = st.color_picker("Text Color", "#FFFFFF")
        preserve_images = st.checkbox("Preserve Original Images", value=True)
        enhance_contrast = st.checkbox("Enhance Text Contrast", value=False)
        
        st.markdown("---")
        st.markdown("### Advanced Options")
        border_detection = st.checkbox("Detect and Convert Borders", value=True)
        table_detection = st.checkbox("Detect and Convert Tables", value=True)
    
    return {
        "bg_color": bg_color,
        "text_color": text_color,
        "preserve_images": preserve_images,
        "enhance_contrast": enhance_contrast,
        "border_detection": border_detection,
        "table_detection": table_detection
    }

def show_app_header():
    """Display the application header and description."""
    st.title("🌙 DarcDocs")
    st.subheader("Convert PDFs to Dark Mode")
    
    st.markdown("""
    DarcDocs transforms your PDFs into dark mode for comfortable reading:
    - ⚫ Black backgrounds
    - ⚪ White text
    - 🖼️ Preserved images
    - 📏 White borders
    """)

def show_file_details(uploaded_file):
    """Display details about the uploaded file."""
    file_details = {
        "Filename": uploaded_file.name,
        "File size": f"{uploaded_file.size / 1024:.2f} KB"
    }
    st.write("**File Details:**")
    for key, value in file_details.items():
        st.write(f"- {key}: {value}")

def show_success_message(message="Conversion complete!"):
    """Display a success message."""
    st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)

def show_error_message(message="Conversion failed. Please try another PDF."):
    """Display an error message."""
    st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)

def create_upload_area(label="Drag and drop your PDF here", accept_multiple=False, key="pdf_uploader"):
    """Create a file upload area without the dotted border."""
    # Removed the upload-area div wrapper
    if accept_multiple:
        uploaded_files = st.file_uploader(label, type="pdf", accept_multiple_files=True, key=key)
    else:
        uploaded_files = st.file_uploader(label, type="pdf", key=key)
    
    return uploaded_files