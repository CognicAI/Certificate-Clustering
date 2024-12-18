from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import base64
import io
import pdf2image
import shutil

# Load environment variables
load_dotenv()

# Configure generative AI
API_KEY = os.getenv("key")
if not API_KEY:
    raise ValueError("Google API Key not found. Please set it in the .env file.")
genai.configure(api_key=API_KEY)

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = {}

def process_uploaded_pdf(uploaded_file):
    """
    Converts uploaded PDF into base64-encoded image parts for generative AI processing.
    """
    if not uploaded_file:
        raise FileNotFoundError("No file uploaded.")
    try:
        # Convert PDF to images
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]

        # Convert the first page to a base64-encoded JPEG
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        return {
            "images": images,  # Store all pages as images
            "first_page": first_page,
            "content": [{
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }]
        }
    except Exception as e:
        raise ValueError(f"Error processing PDF: {e}")

def get_company_name_from_pdf(pdf_content):
    """
    Use Gemini 1.5 Flash to extract company name from the PDF content.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Extract the company name from the provided certificate text."
        response = model.generate_content([prompt, pdf_content[0]])  # Provide the text as input to the AI model
        company_name = response.text.strip()
        return company_name
    except Exception as e:
        return f"Error extracting company name: {e}"

def save_certificate_to_company_folder(certificate, company_name):
    """
    Save the certificate PDF to a folder based on the company name.
    Create a new folder if necessary.
    """
    # Create a folder if it doesn't exist
    folder_path = os.path.join("certificates", company_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Save the PDF to the folder
    certificate.seek(0)  # Reset the file pointer to the beginning
    with open(os.path.join(folder_path, f"{company_name}_certificate.pdf"), "wb") as f:
        f.write(certificate.read())

    return folder_path

def create_streamlit_ui():
    """
    Creates the Streamlit interface for segregating certificates.
    """
    st.set_page_config(page_title="Certificate Segregator", layout="wide")
    st.title("🏅 Certificate Segregator")
    st.markdown(
        "Upload your certificates (PDF format), and the app will segregate them into folders based on company names."
    )

    # Input file uploader
    uploaded_files = st.file_uploader(
        "Upload Your Certificates (PDF format only):",
        type=["pdf"],
        accept_multiple_files=True
    )

    # Process the certificates when the "Submit" button is clicked
    if st.button("Submit"):
        if uploaded_files:
            for file in uploaded_files:
                try:
                    # Process the uploaded PDF
                    pdf_data = process_uploaded_pdf(file)
                    pdf_content = pdf_data["content"]
                    
                    # Extract the company name using Gemini
                    company_name = get_company_name_from_pdf(pdf_content)
                    if "Error" not in company_name:
                        # Save the certificate in the appropriate folder
                        folder_path = save_certificate_to_company_folder(file, company_name)
                        st.success(f"Certificate saved in {folder_path}")
                    else:
                        st.warning(f"Could not extract company name for certificate: {file.name}")
                except Exception as e:
                    st.error(f"Error processing certificate {file.name}: {e}")
        else:
            st.warning("Please upload at least one certificate.")

if __name__ == "__main__":
    create_streamlit_ui()
