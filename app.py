import streamlit as st
import fitz  # PyMuPDF
import io
import os
import tempfile
from PIL import Image, ImageOps
import numpy as np
from datetime import datetime

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

def convert_pdf_to_dark_mode(input_file, progress_callback=None):
    """
    Convert a PDF to dark mode:
    - Black background
    - White text
    - Preserved images
    - White borders
    """
    try:
        # Open the PDF
        doc = fitz.open(stream=input_file.read(), filetype="pdf")
        total_pages = len(doc)
        
        # Create a new PDF for the output
        out_doc = fitz.open()
        
        for page_num, page in enumerate(doc):
            # Update progress
            if progress_callback:
                progress_callback((page_num + 1) / total_pages)
            
            # Create a new page in the output document
            out_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Get the page dimensions
            page_width = page.rect.width
            page_height = page.rect.height
            
            # First, fill the entire page with black
            out_page.draw_rect(fitz.Rect(0, 0, page_width, page_height), color=(0, 0, 0), fill=(0, 0, 0))
            
            try:
                # Process text: extract and redraw in white
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
                                        color=(1, 1, 1)  # White color
                                    )
                                except RuntimeError as font_error:
                                    # If original font fails, use a fallback font
                                    if "FT_New_Memory_Face" in str(font_error):
                                        out_page.insert_text(
                                            bbox.tl,
                                            text,
                                            fontname="helv",  # Use Helvetica as fallback
                                            fontsize=span["size"],
                                            color=(1, 1, 1)
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
                                # Draw white border
                                out_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            except Exception as border_error:
                # If border detection fails, continue with the rest of the process
                st.warning(f"Border detection failed on page {page_num+1}. Some borders may not be converted.")
        
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

def main():
    st.title("🌙 DarcDocs")
    st.subheader("Convert PDFs to Dark Mode")
    
    st.markdown("""
    DarcDocs transforms your PDFs into dark mode for comfortable reading:
    - ⚫ Black backgrounds
    - ⚪ White text
    - 🖼️ Preserved images
    - 📏 White borders
    """)
    
    # File uploader
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drag and drop your PDF here", type="pdf")
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
                progress_callback=lambda p: progress_bar.progress(p)
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
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ by DarcDocs")

if __name__ == "__main__":
    main()