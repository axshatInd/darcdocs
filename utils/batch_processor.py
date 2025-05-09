import streamlit as st
import io
import zipfile
from datetime import datetime
from .pdf_processor import convert_pdf_to_dark_mode

def process_batch(uploaded_files, bg_color, text_color, preserve_images, enhance_contrast, 
                 border_detection, table_detection, use_image_conversion=False, image_quality=2.0):
    """Process multiple PDF files and return them as a zip file."""
    # Create a BytesIO object to store the zip file
    zip_buffer = io.BytesIO()
    
    # Create a ZipFile object
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Process each PDF file
        for i, uploaded_file in enumerate(uploaded_files):
            # Update the status
            st.text(f"Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
            
            # Convert the PDF to dark mode
            result = convert_pdf_to_dark_mode(
                uploaded_file,
                bg_color=bg_color,
                text_color=text_color,
                preserve_images=preserve_images,
                enhance_contrast=enhance_contrast,
                border_detection=border_detection,
                table_detection=table_detection,
                use_image_conversion=use_image_conversion,
                image_quality=image_quality
            )
            
            if result:
                # Generate a filename for the output
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"dark_mode_{timestamp}_{uploaded_file.name}"
                
                # Add the PDF to the zip file
                zip_file.writestr(output_filename, result.getvalue())
    
    # Reset the buffer position to the beginning
    zip_buffer.seek(0)
    return zip_buffer