import os
import re
import google.generativeai as genai
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pdf2image import convert_from_path
from dotenv import load_dotenv
# Configure Google Gemini API
# Load
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# SMTP Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Use your email provider's SMTP server
SMTP_PORT = 465  # Use 587 for TLS, 465 for SSL
SENDER_EMAIL = "subashjipbk@gmail.com"
SENDER_PASSWORD = "lgxo yjum jluw bqgc"  # Enable 'App Passwords' if using Gmail

# Function to extract text using Gemini
def extract_text_from_pdf_with_gemini(pdf_path):
    images = convert_from_path(pdf_path, poppler_path=r"C:\\Users\\lenovo\\Downloads\\Release-24.08.0-0\\poppler-24.08.0\\Library\\bin")
    
    if not images:
        return "Error: No pages found in PDF."
    
    img = images[0]  # Use the first page
    
    model = genai.GenerativeModel("gemini-1.5-flash")  
    response = model.generate_content([img])  
    
    return response.text if hasattr(response, 'text') else "No text extracted"

# Aadhaar Validation
def validate_aadhar(text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""Extract Aadhaar number from the following text:
    Only return the aadhar number if it is valid.and in correct format(XXXX XXXX XXXX).
    Text: {text}
    """
    response = model.generate_content([prompt])
    return response.text if hasattr(response, 'text') else None
# PAN Validation
def validate_pan(text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""Extract PAN number from the following text:
    Only return the PAN number if it is valid.and in correct format(ABCDE1234F)).
    Text: {text}
    """
    response = model.generate_content([prompt])
    return response.text if hasattr(response, 'text') else None

# Function to send email via SMTP
def send_verification_email(receiver_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        
        print(f"Verification email sent to {receiver_email} ✅")
    except Exception as e:
        print(f"Failed to send email ❌: {e}")

# Verify Aadhaar & PAN
def verify_documents(aadhar_pdf, pan_pdf, user_email):
    aadhar_text = extract_text_from_pdf_with_gemini(aadhar_pdf)
    pan_text = extract_text_from_pdf_with_gemini(pan_pdf)

    aadhar_number = validate_aadhar(aadhar_text)
    pan_number = validate_pan(pan_text)

    status = "Verified" if aadhar_number and pan_number else "Rejected"

    email_message = f"""Dear User,

Your document verification result:

Aadhaar: {aadhar_number if aadhar_number else 'Invalid'}
PAN: {pan_number if pan_number else 'Invalid'}
Verification Status: {status}

Thank you,
Verification Team
"""

    send_verification_email(user_email, "Document Verification Result", email_message)

    return {"Aadhaar": aadhar_number, "PAN": pan_number, "Status": status}
