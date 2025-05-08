import streamlit as st
from datetime import datetime
import io

# Import modules from utils package
from utils.ui_components import (
    setup_page_config, apply_custom_css, create_sidebar, 
    show_app_header, show_file_details, show_success_message,
    show_error_message, create_upload_area
)
from utils.pdf_processor import convert_pdf_to_dark_mode, preview_pdf
from utils.batch_processor import process_batch

def main():
    # Set up the page
    setup_page_config()
    apply_custom_css()
    
    # Show app header
    show_app_header()
    
    # Create sidebar and get options
    options = create_sidebar()
    
    # Add tabs for single file and batch processing
    tab1, tab2 = st.tabs(["Single PDF", "Batch Processing"])
    
    # Single PDF processing tab
    with tab1:
        # File uploader
        uploaded_file = create_upload_area(key="single_pdf")
        
        if uploaded_file is not None:
            # Display file info
            show_file_details(uploaded_file)
            
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
                    **options
                )
                
                if result:
                    # Generate a filename for the output
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"dark_mode_{timestamp}_{uploaded_file.name}"
                    
                    # Success message
                    show_success_message()
                    
                    # Download button
                    st.download_button(
                        label="Download Dark Mode PDF",
                        data=result,
                        file_name=output_filename,
                        mime="application/pdf"
                    )
                    
                    # Preview (optional)
                    with st.expander("Preview (first page only)"):
                        img_data = preview_pdf(result)
                        if img_data:
                            st.image(img_data, caption="First Page Preview")
                else:
                    show_error_message()
                
                # Reset progress
                progress_bar.empty()
                status_text.empty()
    
    # Batch processing tab
    with tab2:
        uploaded_files = create_upload_area(
            label="Drag and drop multiple PDFs here", 
            accept_multiple=True, 
            key="batch_pdfs"
        )
        
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
                    **options
                )
                
                # Success message
                show_success_message("Batch conversion complete!")
                
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