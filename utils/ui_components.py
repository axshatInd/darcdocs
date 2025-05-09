import streamlit as st

def setup_page_config():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="DarcDocs - PDF Customizer",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "# DarcDocs\nTransform your PDFs with custom colors for comfortable reading in any environment."
        }
    )

def apply_custom_css():
    """Apply custom CSS for enhanced UI."""
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            background-color: #f5f7fa;
            color: #333;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            padding-top: 0;
        }
        
        /* Page load animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            margin-top: 0;
            animation: fadeIn 0.6s ease-out;
        }
        
        /* Glass effect for containers */
        .glass-container {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Header styling */
        h1, h2, h3 {
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-top: 0.5rem;
            color: #333;
        }
        
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        h2 {
            font-size: 1.8rem !important;
        }
        
        h3 {
            font-size: 1.4rem !important;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #ffffff;
            color: #000000;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 500;
            border: 1px solid rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .stButton>button:hover {
            background-color: #f8f9fa;
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.1);
        }
        
        /* Message styling */
        .success-message {
            background-color: rgba(46, 204, 113, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: #ffffff;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-weight: 500;
            animation: fadeIn 0.5s ease-out;
        }
        
        .error-message {
            background-color: rgba(231, 76, 60, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: #ffffff;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-weight: 500;
            animation: fadeIn 0.5s ease-out;
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #4b6cb7, #182848);
        }
        
        /* Sidebar styling */
        .css-1d391kg, .css-12oz5g7 {
            background-color: #1E1E1E;
        }
        
        /* Fix sidebar text color */
        section[data-testid="stSidebar"] {
            color: #ffffff !important;
        }
        
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {
            color: #ffffff !important;
        }
        
        /* Reduce sidebar top padding */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Reduce space in sidebar elements */
        .sidebar .element-container {
            margin-bottom: 0.5rem;
        }
        
        /* File uploader styling */
        .stFileUploader > div > button {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #4b6cb7;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff;
            color: #000000 !important;
            border-radius: 8px;
            padding: 10px 16px;
            border: 1px solid rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #4b6cb7 !important;
            color: #ffffff !important;
            font-weight: 600;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create the sidebar with customization options."""
    with st.sidebar:
        st.markdown('<h2 style="text-align: center; margin-top: -40px;">Color Studio</h2>', unsafe_allow_html=True)
        
        st.markdown('### Color Palette')
        bg_color = st.color_picker("Background Color", "#000000")
        text_color = st.color_picker("Text Color", "#FFFFFF")
        
        st.markdown('### Image Settings')
        preserve_images = st.checkbox("Preserve Original Images", value=True)
        enhance_contrast = st.checkbox("Enhance Text Contrast", value=False)
        
        st.markdown("---")
        st.markdown("### Advanced Options")
        border_detection = st.checkbox("Detect and Convert Borders", value=True)
        table_detection = st.checkbox("Detect and Convert Tables", value=True)
        
        # New option for image-based conversion
        st.markdown("### Layout Options")
        use_image_conversion = st.checkbox("Preserve Layout (Image-Based)", value=False, 
                                          help="Use image-based conversion to preserve exact layout and alignment. May affect text sharpness.")
        
        # Image quality slider (only shown when image-based conversion is selected)
        image_quality = 2.0
        if use_image_conversion:
            image_quality = st.slider("Image Quality", min_value=1.0, max_value=4.0, value=2.0, step=0.5,
                                     help="Higher values produce sharper text but larger files")
        
        # Preview box
        st.markdown("### Live Preview")
        preview_html = f"""
        <div class="glass-container" style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin-top: 10px;">
            <p style="color: {text_color}; margin: 0;">Sample Text Preview</p>
        </div>
        """
        st.markdown(preview_html, unsafe_allow_html=True)
    
    return {
        "bg_color": bg_color,
        "text_color": text_color,
        "preserve_images": preserve_images,
        "enhance_contrast": enhance_contrast,
        "border_detection": border_detection,
        "table_detection": table_detection,
        "use_image_conversion": use_image_conversion,
        "image_quality": image_quality
    }

def show_app_header():
    """Display the application header and description."""
    # Add padding at the top to move the header down
    st.markdown('<div style="padding-top: 20px;"></div>', unsafe_allow_html=True)
    
    # Update the heading to DarcDocs with PDF Color Customizer as subtitle
    st.markdown('<h1 style="text-align: center; font-size: 3rem;">DarcDocs</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #4b6cb7; margin-top: -10px; margin-bottom: 20px;">PDF Color Customizer</h3>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-container">
        <h3 style="margin-top: 0;">Transform Your Reading Experience</h3>
        <p>DarcDocs lets you personalize PDFs with custom colors for comfortable reading in any environment:</p>
        <ul>
            <li><strong>Custom Background Colors</strong> - From pitch black to any color you prefer</li>
            <li><strong>Custom Text Colors</strong> - Choose the perfect text color for readability</li>
            <li><strong>Preserved Images</strong> - Keep images in their original form</li>
            <li><strong>Enhanced Borders & Tables</strong> - Automatically detect and convert structural elements</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def show_file_details(uploaded_file):
    """Display details about the uploaded file."""
    file_details = {
        "Filename": uploaded_file.name,
        "File size": f"{uploaded_file.size / 1024:.2f} KB"
    }
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.markdown("### File Details")
    for key, value in file_details.items():
        st.write(f"- **{key}:** {value}")
    st.markdown('</div>', unsafe_allow_html=True)

def show_success_message(message="Conversion complete!"):
    """Display a success message."""
    st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)

def show_error_message(message="Conversion failed. Please try another PDF."):
    """Display an error message."""
    st.markdown(f'<div class="error-message">{message}</div>', unsafe_allow_html=True)

def create_upload_area(label="Drag and drop your PDF here", accept_multiple=False, key="pdf_uploader"):
    """Create a file upload area with enhanced styling."""
    st.markdown(f"""
    <div class="glass-container" style="text-align: center; margin-bottom: 10px;">
        <h3>{label}</h3>
        <p style="color: #4b6cb7; font-size: 0.9rem;">Click to browse or drag and drop</p>
    </div>
    """, unsafe_allow_html=True)
    
    if accept_multiple:
        uploaded_files = st.file_uploader(
            label, 
            type="pdf", 
            accept_multiple_files=True, 
            key=key,
            label_visibility="collapsed"  # Hide the label but keep it for accessibility
        )
    else:
        uploaded_files = st.file_uploader(
            label, 
            type="pdf", 
            key=key,
            label_visibility="collapsed"  # Hide the label but keep it for accessibility
        )
    
    return uploaded_files