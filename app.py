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
    tab1, tab2 = st.tabs(["✨ Single PDF", "📚 Batch Processing"])
    
    # Single PDF processing tab
    with tab1:
        # File uploader
        uploaded_file = create_upload_area(label="Transform Your PDF", key="single_pdf")
        
        if uploaded_file is not None:
            # Display file info
            show_file_details(uploaded_file)
            
            # Process button
            if st.button("✨ Transform PDF with Custom Colors"):
                # Progress bar
                st.markdown("### 🔄 Processing Your PDF")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Applying your custom colors...")
                
                # Process the PDF
                result = convert_pdf_to_dark_mode(
                    uploaded_file,
                    progress_callback=lambda p: progress_bar.progress(p),
                    **options
                )
                
                if result:
                    # Generate a filename for the output
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"custom_{timestamp}_{uploaded_file.name}"
                    
                    # Success message
                    show_success_message("✨ Transformation complete! Your PDF is ready to download.")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Transformed PDF",
                        data=result,
                        file_name=output_filename,
                        mime="application/pdf"
                    )
                    
                    # Preview (optional)
                    with st.expander("👁️ Preview (first page only)"):
                        img_data = preview_pdf(result)
                        if img_data:
                            st.image(img_data, caption="First Page Preview")
                else:
                    show_error_message("Transformation failed. Please try another PDF or adjust your settings.")
                
                # Reset progress
                progress_bar.empty()
                status_text.empty()
    
    # Batch processing tab
    with tab2:
        uploaded_files = create_upload_area(
            label="Transform Multiple PDFs", 
            accept_multiple=True, 
            key="batch_pdfs"
        )
        
        if uploaded_files:
            st.markdown("### 📚 Selected Files")
            st.markdown('<div style="background-color: rgba(187, 134, 252, 0.1); padding: 15px; border-radius: 8px;">', unsafe_allow_html=True)
            st.write(f"**{len(uploaded_files)} files ready for transformation:**")
            for file in uploaded_files:
                st.write(f"- **{file.name}** ({file.size / 1024:.2f} KB)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("✨ Transform All PDFs"):
                # Create a status area
                st.markdown("### 🔄 Processing Your PDFs")
                status_area = st.empty()
                
                # Process the batch
                status_area.text("Applying your custom colors to all files...")
                zip_buffer = process_batch(
                    uploaded_files,
                    **options
                )
                
                # Success message
                show_success_message("✨ Batch transformation complete! Your PDFs are ready to download.")
                
                # Generate a filename for the zip
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"custom_pdfs_{timestamp}.zip"
                
                # Download button for the zip file
                st.download_button(
                    label="📥 Download All Transformed PDFs",
                    data=zip_buffer,
                    file_name=zip_filename,
                    mime="application/zip"
                )
                
                # Clear the status area
                status_area.empty()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #BB86FC;">
        <p>&copy; DarcDocs 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()