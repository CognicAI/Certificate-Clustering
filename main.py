from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import base64
import io
import pdf2image
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure generative AI
API_KEY = os.getenv("key")
if not API_KEY:
    st.error("❌ Google API Key not found. Please set it in the .env file.")
    st.stop()

genai.configure(api_key=API_KEY)

# Constants
MAX_FILE_SIZE_MB = 200
SUPPORTED_FORMATS = ["pdf"]
CERTIFICATES_DIR = "certificates"
GEMINI_MODEL = "gemini-1.5-flash"

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = {}
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "processing_stats" not in st.session_state:
    st.session_state.processing_stats = {
        "total_files": 0,
        "successful": 0,
        "failed": 0,
        "start_time": None,
        "detailed_timing": [],
        "average_times": {
            "pdf_processing": 0,
            "ai_extraction": 0,
            "file_saving": 0,
            "total_per_file": 0
        }
    }

def validate_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate uploaded file for size and format.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
    
    # Check file format
    if uploaded_file.type != "application/pdf":
        return False, "Only PDF files are supported"
    
    return True, ""

def clean_company_name(company_name: str) -> str:
    """
    Clean and normalize company name for folder creation.
    
    Args:
        company_name: Raw company name from AI extraction
        
    Returns:
        Cleaned company name safe for filesystem
    """
    if not company_name:
        return "Unknown_Company"
    
    # Remove common prefixes/suffixes and clean
    cleaned = re.sub(r'^(The\s+|A\s+)', '', company_name, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+(Inc\.?|LLC\.?|Ltd\.?|Corporation|Corp\.?|Company|Co\.?)$', '', cleaned, flags=re.IGNORECASE)
    
    # Replace invalid filesystem characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', cleaned)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    # Limit length
    return cleaned[:50] if len(cleaned) > 50 else cleaned

@st.cache_data(ttl=300)  # Cache for 5 minutes
def process_uploaded_pdf(uploaded_file_bytes: bytes, file_name: str) -> Tuple[Dict, float]:
    """
    Converts uploaded PDF into base64-encoded image parts for generative AI processing.
    
    Args:
        uploaded_file_bytes: PDF file content as bytes
        file_name: Name of the uploaded file
        
    Returns:
        Tuple of (Dictionary containing processed PDF data, processing time in seconds)
        
    Raises:
        ValueError: If PDF processing fails
    """
    start_time = time.time()
    try:
        # Convert PDF to images with optimized settings
        images = pdf2image.convert_from_bytes(
            uploaded_file_bytes,
            dpi=150,  # Reduced DPI for faster processing
            first_page=1,
            last_page=2,  # Only process first 2 pages
            fmt='JPEG'
        )
        
        if not images:
            raise ValueError("No pages found in PDF")
        
        first_page = images[0]

        # Convert the first page to a base64-encoded JPEG with compression
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
        img_byte_arr = img_byte_arr.getvalue()

        result = {
            "images": images,
            "first_page": first_page,
            "content": [{
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }],
            "file_name": file_name
        }
        
        processing_time = time.time() - start_time
        return result, processing_time
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing PDF {file_name}: {str(e)} (took {processing_time:.2f}s)")
        raise ValueError(f"Error processing PDF: {e}")

def get_company_name_from_pdf(pdf_content: List[Dict], file_name: str, max_retries: int = 3) -> Tuple[str, float]:
    """
    Use Gemini 1.5 Flash to extract company name from the PDF content with retry logic.
    
    Args:
        pdf_content: List containing the PDF content
        file_name: Name of the file being processed
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (extracted company name or error message, processing time in seconds)
    """
    start_time = time.time()
    
    enhanced_prompt = """
    Analyze this certificate image carefully and extract ONLY the company/organization name that issued this certificate.
    
    Instructions:
    1. Look for the PRIMARY company name that appears as the issuer/provider of the certificate
    2. This is usually at the top of the certificate or in a prominent position
    3. Return ONLY the company name, no additional text or explanations
    4. If multiple company names appear, choose the main issuer (not partners or sponsors)
    5. Remove common business suffixes like Inc., LLC, Ltd., Corp., Corporation, Company, etc.
    6. If no clear company name is found, return "Unknown_Company"
    
    Common certificate types and their issuers:
    - Training certificates: Look for the training provider/platform name
    - Professional certifications: Look for the certifying organization
    - Course completion: Look for the educational institution or platform
    - Achievement certificates: Look for the awarding organization
    
    Examples:
    - "Google LLC Certificate of Completion" → return "Google"
    - "Microsoft Corporation Training Certificate" → return "Microsoft"  
    - "Amazon Web Services Certification" → return "Amazon Web Services"
    - "Coursera Certificate" → return "Coursera"
    - "edX Verified Certificate" → return "edX"
    - "LinkedIn Learning Certificate" → return "LinkedIn Learning"
    - "Udemy Certificate of Completion" → return "Udemy"
    
    Extract the company name:
    """
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content([enhanced_prompt, pdf_content[0]])
            
            if response and response.text:
                company_name = response.text.strip()
                # Remove any quotes or extra formatting
                company_name = company_name.strip('"\'`')
                
                # Additional cleaning
                company_name = clean_company_name(company_name)
                
                if company_name and company_name != "Unknown_Company" and len(company_name) > 1:
                    processing_time = time.time() - start_time
                    logger.info(f"Successfully extracted company name '{company_name}' from {file_name} in {processing_time:.2f}s")
                    return company_name, processing_time
            
            logger.warning(f"Attempt {attempt + 1}: No valid company name extracted from {file_name}")
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {file_name}: {str(e)}")
            if attempt == max_retries - 1:
                processing_time = time.time() - start_time
                return f"Error extracting company name: {e}", processing_time
            time.sleep(1)  # Brief delay before retry
    
    processing_time = time.time() - start_time
    return "Unknown_Company", processing_time

def save_certificate_to_company_folder(certificate_bytes: bytes, company_name: str, original_filename: str) -> Tuple[str, float]:
    """
    Save the certificate PDF to a folder based on the company name.
    
    Args:
        certificate_bytes: PDF file content as bytes
        company_name: Cleaned company name
        original_filename: Original name of the uploaded file
        
    Returns:
        Tuple of (Path to the saved certificate, processing time in seconds)
        
    Raises:
        OSError: If file creation fails
    """
    start_time = time.time()
    try:
        # Create folder path
        folder_path = os.path.join(CERTIFICATES_DIR, company_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include microseconds
        base_name = os.path.splitext(original_filename)[0]
        base_filename = f"{base_name}_{timestamp}.pdf"
        file_path = os.path.join(folder_path, base_filename)
        
        # Ensure the filename is truly unique by adding a counter if needed
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base_name}_{timestamp}_{counter}.pdf"
            file_path = os.path.join(folder_path, filename)
            counter += 1
        
        # Save the PDF
        with open(file_path, "wb") as f:
            f.write(certificate_bytes)
        
        processing_time = time.time() - start_time
        logger.info(f"Certificate saved: {file_path} (took {processing_time:.2f}s)")
        return file_path, processing_time
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error saving certificate: {str(e)} (took {processing_time:.2f}s)")
        raise OSError(f"Failed to save certificate: {e}")

def display_folder_structure():
    """Display the current folder structure of organized certificates."""
    if os.path.exists(CERTIFICATES_DIR):
        st.subheader("📁 Current Folder Structure")
        
        # Get all company folders
        company_folders = [d for d in os.listdir(CERTIFICATES_DIR) 
                          if os.path.isdir(os.path.join(CERTIFICATES_DIR, d))]
        
        if company_folders:
            for company in sorted(company_folders):
                company_path = os.path.join(CERTIFICATES_DIR, company)
                certificates = [f for f in os.listdir(company_path) if f.endswith('.pdf')]
                
                with st.expander(f"📂 {company} ({len(certificates)} certificates)"):
                    for cert in sorted(certificates):
                        cert_path = os.path.join(company_path, cert)
                        file_size = os.path.getsize(cert_path) / (1024 * 1024)  # MB
                        mod_time = datetime.fromtimestamp(os.path.getmtime(cert_path))
                        st.write(f"📄 {cert} ({file_size:.1f}MB) - Added: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("No certificates organized yet. Upload and process some certificates to see the folder structure.")
    else:
        st.info("Certificates folder not created yet.")

def display_performance_analytics():
    """Display detailed performance analytics and timing metrics."""
    if 'detailed_timing' in st.session_state and st.session_state.detailed_timing:
        st.subheader("⏱️ Performance Analytics")
        
        # Overall statistics
        timing_data = st.session_state.detailed_timing
        average_times = st.session_state.get('average_times', {})
        
        if average_times:
            st.markdown("### 📊 Average Processing Times")
            col1, col2, col3, col4 = st.columns(4)
            
            operations = ['PDF Processing', 'AI Extraction', 'File Saving', 'Total']
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            for i, (col, operation) in enumerate(zip([col1, col2, col3, col4], operations)):
                if operation in average_times and average_times[operation]:
                    avg_time = sum(average_times[operation]) / len(average_times[operation])
                    with col:
                        st.metric(
                            label=operation,
                            value=f"{avg_time:.2f}s",
                            delta=f"{len(average_times[operation])} files"
                        )
        
        # Detailed breakdown
        with st.expander("📈 Detailed Processing Breakdown"):
            # Create a DataFrame for better visualization
            breakdown_data = []
            for entry in timing_data:
                row = {
                    'File': entry['filename'],
                    'Company': entry['company'],
                    'PDF (s)': f"{entry['times'].get('PDF Processing', 0):.2f}",
                    'AI (s)': f"{entry['times'].get('AI Extraction', 0):.2f}",
                    'Save (s)': f"{entry['times'].get('File Saving', 0):.2f}",
                    'Total (s)': f"{entry['times'].get('Total', 0):.2f}",
                    'Time': entry['timestamp']
                }
                breakdown_data.append(row)
            
            if breakdown_data:
                st.dataframe(breakdown_data, use_container_width=True)
        
        # Performance insights
        with st.expander("💡 Performance Insights"):
            if average_times:
                # Find bottleneck
                bottleneck_times = {
                    'PDF Processing': sum(average_times.get('PDF Processing', [])) / len(average_times.get('PDF Processing', [1])),
                    'AI Extraction': sum(average_times.get('AI Extraction', [])) / len(average_times.get('AI Extraction', [1])),
                    'File Saving': sum(average_times.get('File Saving', [])) / len(average_times.get('File Saving', [1]))
                }
                
                slowest_operation = max(bottleneck_times, key=bottleneck_times.get)
                fastest_operation = min(bottleneck_times, key=bottleneck_times.get)
                
                st.info(f"🐌 **Slowest Operation:** {slowest_operation} ({bottleneck_times[slowest_operation]:.2f}s avg)")
                st.success(f"⚡ **Fastest Operation:** {fastest_operation} ({bottleneck_times[fastest_operation]:.2f}s avg)")
                
                # Recommendations
                if bottleneck_times['AI Extraction'] > 3.0:
                    st.warning("🤖 **AI Extraction is taking longer than expected.** This could be due to:")
                    st.markdown("- Complex certificate layouts")
                    st.markdown("- Network latency to Gemini API")
                    st.markdown("- Large image sizes")
                
                if bottleneck_times['PDF Processing'] > 2.0:
                    st.warning("📄 **PDF Processing is slower than optimal.** Consider:")
                    st.markdown("- Reducing PDF file sizes")
                    st.markdown("- Processing fewer pages if possible")

def display_processing_stats():
    """Display processing statistics in the sidebar."""
    with st.sidebar:
        st.subheader("📊 Processing Statistics")
        stats = st.session_state.processing_stats
        
        if stats["total_files"] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Files", stats["total_files"])
                st.metric("Successful", stats["successful"])
            with col2:
                st.metric("Failed", stats["failed"])
                success_rate = (stats["successful"] / stats["total_files"]) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            if stats["start_time"]:
                elapsed = time.time() - stats["start_time"]
                st.metric("Processing Time", f"{elapsed:.1f}s")
        
        # Show folder statistics
        if os.path.exists(CERTIFICATES_DIR):
            st.subheader("📁 Folder Stats")
            company_folders = [d for d in os.listdir(CERTIFICATES_DIR) 
                              if os.path.isdir(os.path.join(CERTIFICATES_DIR, d))]
            total_certs = 0
            for company in company_folders:
                company_path = os.path.join(CERTIFICATES_DIR, company)
                certs = [f for f in os.listdir(company_path) if f.endswith('.pdf')]
                total_certs += len(certs)
            
            st.metric("Companies", len(company_folders))
            st.metric("Total Certificates", total_certs)

def display_results_summary():
    """Display summary of processed files."""
    if st.session_state.processed_files:
        st.subheader("📋 Processing Results")
        
        # Group by company
        companies = {}
        for result in st.session_state.processed_files:
            company = result.get("company_name", "Unknown")
            if company not in companies:
                companies[company] = []
            companies[company].append(result)
        
        # Display grouped results
        for company, files in companies.items():
            with st.expander(f"🏢 {company} ({len(files)} files)"):
                for file_result in files:
                    status_icon = "✅" if file_result["status"] == "success" else "❌"
                    st.write(f"{status_icon} {file_result['filename']} - {file_result['message']}")

def create_streamlit_ui():
    """
    Creates the enhanced Streamlit interface for segregating certificates.
    """
    st.set_page_config(
        page_title="Certificate Segregator",
        page_icon="🏅",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🏅 Certificate Segregator")
    st.markdown("""
    ### Intelligent Certificate Organization with AI
    Upload your PDF certificates and let AI automatically organize them by company name.
    
    **Features:**
    - 🤖 AI-powered company name extraction
    - 📁 Automatic folder organization
    - ⚡ Batch processing support
    - 📊 Real-time processing statistics
    """)
    
    # Sidebar for configuration and stats
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"**Max file size:** {MAX_FILE_SIZE_MB}MB per file")
        st.info(f"**Supported formats:** {', '.join(SUPPORTED_FORMATS).upper()}")
        
        # Clear results button
        if st.button("🗑️ Clear Results"):
            st.session_state.processed_files = []
            st.session_state.processing_stats = {
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "start_time": None
            }
            st.rerun()
    
    # File uploader with improved UI
    st.subheader("📤 Upload Certificates")
    uploaded_files = st.file_uploader(
        "Choose PDF certificate files:",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=True,
        help=f"Upload one or more PDF certificates (max {MAX_FILE_SIZE_MB}MB each)"
    )
    
    # Display file preview
    if uploaded_files:
        st.subheader(f"📋 Selected Files ({len(uploaded_files)})")
        for i, file in enumerate(uploaded_files):
            file_size_mb = file.size / (1024 * 1024)
            st.write(f"{i+1}. **{file.name}** ({file_size_mb:.1f}MB)")
    
    # Process button
    if st.button("🚀 Process Certificates", type="primary", disabled=not uploaded_files):
        if uploaded_files:
            # Initialize processing
            st.session_state.processing_stats.update({
                "total_files": len(uploaded_files),
                "successful": 0,
                "failed": 0,
                "start_time": time.time()
            })
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            for i, file in enumerate(uploaded_files):
                # Update progress
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {file.name}... ({i+1}/{len(uploaded_files)})")
                
                # Validate file
                is_valid, error_msg = validate_file(file)
                if not is_valid:
                    result = {
                        "filename": file.name,
                        "status": "error",
                        "company_name": "N/A",
                        "message": error_msg
                    }
                    results.append(result)
                    st.session_state.processing_stats["failed"] += 1
                    continue
                
                try:
                    # Track detailed timing for each operation
                    operation_times = {}
                    total_start = time.time()
                    
                    # Read file bytes once
                    file_bytes = file.read()
                    
                    # Process the uploaded PDF and get timing data
                    pdf_data, pdf_time = process_uploaded_pdf(file_bytes, file.name)
                    operation_times['PDF Processing'] = pdf_time
                    pdf_content = pdf_data["content"]
                    
                    # Show certificate preview (optional - can be toggled in sidebar)
                    if st.sidebar.checkbox("Show Certificate Preview", key=f"preview_{i}"):
                        st.image(pdf_data["first_page"], caption=f"Preview: {file.name}", use_column_width=True)
                    
                    # Extract the company name using Gemini and get timing data
                    company_name, ai_time = get_company_name_from_pdf(pdf_content, file.name)
                    operation_times['AI Extraction'] = ai_time
                    
                    if "Error" not in company_name and company_name != "Unknown_Company":
                        # Save the certificate and get timing data
                        file_path, save_time = save_certificate_to_company_folder(
                            file_bytes, company_name, file.name
                        )
                        operation_times['File Saving'] = save_time
                        
                        total_time = time.time() - total_start
                        operation_times['Total'] = total_time
                        
                        # Update session state with timing data
                        if 'detailed_timing' not in st.session_state:
                            st.session_state.detailed_timing = []
                        if 'average_times' not in st.session_state:
                            st.session_state.average_times = {
                                'PDF Processing': [],
                                'AI Extraction': [],
                                'File Saving': [],
                                'Total': []
                            }
                        
                        # Store detailed timing for this file
                        file_timing = {
                            'filename': file.name,
                            'company': company_name,
                            'times': operation_times.copy(),
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        }
                        st.session_state.detailed_timing.append(file_timing)
                        
                        # Update average calculations
                        for operation, time_taken in operation_times.items():
                            st.session_state.average_times[operation].append(time_taken)
                        
                        result = {
                            "filename": file.name,
                            "status": "success",
                            "company_name": company_name,
                            "message": f"Saved to {file_path}",
                            "timing": operation_times
                        }
                        st.session_state.processing_stats["successful"] += 1
                        
                        # Show success with company name and timing
                        st.success(f"✅ {file.name} → **{company_name}** folder")
                        
                        # Display timing breakdown in an expander
                        with st.expander(f"⏱️ Processing Time Breakdown for {file.name}"):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("PDF Processing", f"{pdf_time:.2f}s")
                            with col2:
                                st.metric("AI Extraction", f"{ai_time:.2f}s")
                            with col3:
                                st.metric("File Saving", f"{save_time:.2f}s")
                            with col4:
                                st.metric("Total Time", f"{total_time:.2f}s")
                        
                    else:
                        total_time = time.time() - total_start
                        operation_times['Total'] = total_time
                        
                        result = {
                            "filename": file.name,
                            "status": "warning",
                            "company_name": company_name,
                            "message": "Could not extract company name reliably",
                            "timing": operation_times
                        }
                        st.session_state.processing_stats["failed"] += 1
                        st.warning(f"⚠️ {file.name} → Could not identify company (took {total_time:.2f}s)")
                    
                    results.append(result)
                    
                except Exception as e:
                    result = {
                        "filename": file.name,
                        "status": "error",
                        "company_name": "N/A",
                        "message": f"Processing error: {str(e)}"
                    }
                    results.append(result)
                    st.session_state.processing_stats["failed"] += 1
                    logger.error(f"Error processing {file.name}: {str(e)}")
            
            # Store results
            st.session_state.processed_files.extend(results)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display completion message
            success_count = st.session_state.processing_stats["successful"]
            total_count = st.session_state.processing_stats["total_files"]
            
            if success_count == total_count:
                st.success(f"🎉 Successfully processed all {total_count} certificates!")
            elif success_count > 0:
                st.warning(f"⚠️ Processed {success_count}/{total_count} certificates successfully.")
            else:
                st.error("❌ Failed to process any certificates. Please check the files and try again.")
    
    # Display statistics and results
    display_processing_stats()
    display_results_summary()
    display_performance_analytics()
    display_folder_structure()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ using Streamlit and Google Gemini AI</p>
        <p><small>🔥 Your certificates are being intelligently organized by AI!</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    create_streamlit_ui()
