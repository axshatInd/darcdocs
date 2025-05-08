import streamlit as st
import fitz  # PyMuPDF
import io
import os
import tempfile
from PIL import Image, ImageOps
import numpy as np
from datetime import datetime
import zipfile

# Set page configuration
st.set_page_config(
    page_title="DarcDocs - PDF Dark Mode Converter",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# DarcDocs\nConvert your PDFs to dark mode for comfortable reading."
    }
)

# Custom CSS for dark mode
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
    .upload-area {
        border: 2px dashed #BB86FC;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
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

def is_likely_border(contour, page_width, page_height, threshold=0.8):
    """Determine if a contour is likely a border based on its size relative to the page."""
    x0, y0, x1, y1 = contour
    contour_width = x1 - x0
    contour_height = y1 - y0
    
    # Check if contour spans most of the page width or height
    width_ratio = contour_width / page_width
    height_ratio = contour_height / page_height
    
    # Check if it's a thin line along the edge
    is_horizontal_border = (height_ratio < 0.05 and width_ratio > threshold)
    is_vertical_border = (width_ratio < 0.05 and height_ratio > threshold)
    
    # Check if it's a rectangle that covers most of the page (like a background)
    is_page_border = (width_ratio > threshold and height_ratio > threshold)
    
    return is_horizontal_border or is_vertical_border or is_page_border

def convert_pdf_to_dark_mode(input_file, progress_callback=None, bg_color="#000000", text_color="#FFFFFF", 
                            preserve_images=True, enhance_contrast=False, border_detection=True, table_detection=True):
    """
    Convert a PDF to dark mode:
    - Black background (or custom color)
    - White text (or custom color)
    - Preserved images
    - White borders
    """
    try:
        # Open the PDF
        doc = fitz.open(stream=input_file.read(), filetype="pdf")
        total_pages = len(doc)
        
        # Create a new PDF for the output
        out_doc = fitz.open()
        
        # Convert hex color to RGB tuple (0-1 range)
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
        text_rgb = tuple(int(text_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
        
        for page_num, page in enumerate(doc):
            # Update progress
            if progress_callback:
                progress_callback((page_num + 1) / total_pages)
            
            # Create a new page in the output document
            out_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Get the page dimensions
            page_width = page.rect.width
            page_height = page.rect.height
            
            # First, fill the entire page with the background color
            out_page.draw_rect(fitz.Rect(0, 0, page_width, page_height), color=bg_rgb, fill=bg_rgb)
            
            try:
                # Process text: extract and redraw with custom color
                text_blocks = page.get_text("dict")["blocks"]
                for block in text_blocks:
                    if block["type"] == 0:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"]
                                bbox = fitz.Rect(span["bbox"])
                                try:
                                    # Try to use the original font
                                    out_page.insert_text(
                                        bbox.tl,  # top-left point
                                        text,
                                        fontname=span["font"],
                                        fontsize=span["size"],
                                        color=text_rgb  # Use custom text color
                                    )
                                except RuntimeError as font_error:
                                    # If original font fails, use a fallback font
                                    if "FT_New_Memory_Face" in str(font_error):
                                        out_page.insert_text(
                                            bbox.tl,
                                            text,
                                            fontname="helv",  # Use Helvetica as fallback
                                            fontsize=span["size"],
                                            color=text_rgb  # Use custom text color
                                        )
                                    else:
                                        # Re-raise if it's not a font error
                                        raise
            except Exception as text_error:
                # If text extraction fails, try to render the page as an image
                st.warning(f"Text extraction failed on page {page_num+1}, using image-based conversion.")
                pix = page.get_pixmap(alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert to grayscale, invert colors, and convert back to RGB
                img_gray = ImageOps.grayscale(img)
                img_inverted = ImageOps.invert(img_gray)
                img_rgb = img_inverted.convert("RGB")
                
                # Convert PIL Image to bytes
                img_bytes = io.BytesIO()
                img_rgb.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                
                # Insert the inverted image
                out_page.insert_image(fitz.Rect(0, 0, page_width, page_height), stream=img_bytes.getvalue())
            
            # Only process images if preserve_images is True
            if preserve_images:
                try:
                    # Process images: extract and redraw as is
                    image_list = page.get_images(full=True)
                    for img_index, img_info in enumerate(image_list):
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convert image bytes to PIL Image
                        img = Image.open(io.BytesIO(image_bytes))
                        
                        # Get image position on the page
                        img_rect = page.get_image_bbox(img_info)
                        
                        # Insert the image back into the new page
                        out_page.insert_image(img_rect, stream=image_bytes)
                except Exception as img_error:
                    # If image extraction fails, continue with the rest of the process
                    st.warning(f"Image extraction failed on page {page_num+1}. Some images may not be preserved.")
            
            # Only process borders if border_detection is True
            if border_detection:
                try:
                    # Process borders: detect and convert to white
                    # Get all drawings on the page
                    paths = page.get_drawings()
                    for path in paths:
                        for item in path["items"]:
                            if item[0] == "re":  # Rectangle
                                rect = fitz.Rect(item[1])
                                # Check if this rectangle is likely a border
                                if is_likely_border(rect, page_width, page_height):
                                    # Draw border with text color
                                    out_page.draw_rect(rect, color=text_rgb, fill=text_rgb)
                except Exception as border_error:
                    # If border detection fails, continue with the rest of the process
                    st.warning(f"Border detection failed on page {page_num+1}. Some borders may not be converted.")
            
            # Process tables if table_detection is True
            if table_detection:
                try:
                    # Simple table detection (looking for grid-like structures)
                    # This is a simplified approach - real table detection would be more complex
                    paths = page.get_drawings()
                    for path in paths:
                        for item in path["items"]:
                            if item[0] == "l":  # Line
                                # Draw lines with text color
                                out_page.draw_line(
                                    fitz.Point(item[1][0], item[1][1]),
                                    fitz.Point(item[1][2], item[1][3]),
                                    color=text_rgb
                                )
                except Exception as table_error:
                    # If table detection fails, continue with the rest of the process
                    pass
        
        # Save the output PDF to a bytes buffer
        output_buffer = io.BytesIO()
        out_doc.save(output_buffer)
        output_buffer.seek(0)
        
        # Close the documents
        doc.close()
        out_doc.close()
        
        return output_buffer
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

def process_batch(uploaded_files, bg_color, text_color, preserve_images, enhance_contrast, border_detection, table_detection):
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
                table_detection=table_detection
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

def main():
    st.title("🌙 DarcDocs")
    st.subheader("Convert PDFs to Dark Mode")
    
    # Add a sidebar for customization options
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
    
    st.markdown("""
    DarcDocs transforms your PDFs into dark mode for comfortable reading:
    - ⚫ Black backgrounds
    - ⚪ White text
    - 🖼️ Preserved images
    - 📏 White borders
    """)
    
    # Add tabs for single file and batch processing
    tab1, tab2 = st.tabs(["Single PDF", "Batch Processing"])
    
    # Single PDF processing tab
    with tab1:
        # File uploader
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drag and drop your PDF here", type="pdf", key="single_pdf")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file is not None:
            # Display file info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.write("**File Details:**")
            for key, value in file_details.items():
                st.write(f"- {key}: {value}")
            
            # Process button
            if st.button("Convert to Dark Mode"):
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Processing PDF...")
                
                # Process the PDF
                result = convert_pdf_to_dark_mode(
                    uploaded_file,
                    progress_callback=lambda p: progress_bar.progress(p),
                    bg_color=bg_color,
                    text_color=text_color,
                    preserve_images=preserve_images,
                    enhance_contrast=enhance_contrast,
                    border_detection=border_detection,
                    table_detection=table_detection
                )
                
                if result:
                    # Generate a filename for the output
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"dark_mode_{timestamp}_{uploaded_file.name}"
                    
                    # Success message
                    st.markdown(f'<div class="success-message">✅ Conversion complete!</div>', unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        label="Download Dark Mode PDF",
                        data=result,
                        file_name=output_filename,
                        mime="application/pdf"
                    )
                    
                    # Preview (optional)
                    with st.expander("Preview (first page only)"):
                        try:
                            # Create a temporary file to save the PDF for preview
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                tmp_file.write(result.getvalue())
                                tmp_path = tmp_file.name
                            
                            # Open the PDF and convert first page to image for preview
                            doc = fitz.open(tmp_path)
                            if len(doc) > 0:
                                page = doc[0]
                                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                img_data = pix.tobytes("png")
                                st.image(img_data, caption="First Page Preview")
                            doc.close()
                            
                            # Clean up the temporary file
                            os.unlink(tmp_path)
                        except Exception as e:
                            st.error(f"Error generating preview: {str(e)}")
            else:
                st.markdown(f'<div class="error-message">❌ Conversion failed. Please try another PDF.</div>', unsafe_allow_html=True)
            
            # Reset progress
            progress_bar.empty()
            status_text.empty()
    
    # Batch processing tab
    with tab2:
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Drag and drop multiple PDFs here", type="pdf", accept_multiple_files=True, key="batch_pdfs")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} files selected:**")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size / 1024:.2f} KB)")
            
            if st.button("Convert All to Dark Mode"):
                # Create a status area
                status_area = st.empty()
                
                # Process the batch
                status_area.text("Processing batch...")
                zip_buffer = process_batch(
                    uploaded_files,
                    bg_color,
                    text_color,
                    preserve_images,
                    enhance_contrast,
                    border_detection,
                    table_detection
                )
                
                # Success message
                st.markdown(f'<div class="success-message">✅ Batch conversion complete!</div>', unsafe_allow_html=True)
                
                # Generate a filename for the zip
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"dark_mode_batch_{timestamp}.zip"
                
                # Download button for the zip file
                st.download_button(
                    label="Download All Converted PDFs",
                    data=zip_buffer,
                    file_name=zip_filename,
                    mime="application/zip"
                )
                
                # Clear the status area
                status_area.empty()
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ by DarcDocs")

if __name__ == "__main__":
    main()