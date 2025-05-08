import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageOps
import os
import tempfile

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

def preview_pdf(pdf_data):
    """Generate a preview image of the first page of a PDF."""
    try:
        # Create a temporary file to save the PDF for preview
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_data.getvalue())
            tmp_path = tmp_file.name
        
        # Open the PDF and convert first page to image for preview
        doc = fitz.open(tmp_path)
        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()
            
            # Clean up the temporary file
            os.unlink(tmp_path)
            
            return img_data
        else:
            doc.close()
            os.unlink(tmp_path)
            return None
    except Exception as e:
        st.error(f"Error generating preview: {str(e)}")
        return None