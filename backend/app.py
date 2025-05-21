from flask import Flask, request, jsonify, send_from_directory
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
import os
import time
import json
from werkzeug.utils import secure_filename
from sqlalchemy import text
from PIL import Image
from pathlib import Path
from datetime import datetime
from verify import verify_documents
from statements_processor import user_input,get_vector_store,get_text_chunks,get_pdf_text,extract_text_from_image
from dotenv import load_dotenv


# Import our invoice processor module
from invoice_processor import InvoiceProcessor

# --- Import DB and Models ---
from models import db, Users, Invoice, InvoiceData

# --- Flask App Setup ---
app = Flask(__name__)

# --- Configurations ---
app.config['SECRET_KEY'] = 'demo'
app.config['JWT_SECRET_KEY'] = 'supersecret-jwt-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Sainikhil%40333@localhost:3306/invoice_processor'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# Define upload directories
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
AADHAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'aadhar')
PAN_FOLDER = os.path.join(UPLOAD_FOLDER, 'pan')
INVOICE_FOLDER = os.path.join(UPLOAD_FOLDER, 'invoices')
STATEMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'statements')

# Create folders if they don't exist
for folder in [UPLOAD_FOLDER, AADHAR_FOLDER, PAN_FOLDER, INVOICE_FOLDER,STATEMENT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# App Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AADHAR_FOLDER'] = AADHAR_FOLDER
app.config['PAN_FOLDER'] = PAN_FOLDER
app.config['INVOICE_FOLDER'] = INVOICE_FOLDER
app.config['STATEMENT_FOLDER'] = STATEMENT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# API key for Google Gemini AI
load_dotenv()
GEMINI_API_KEY= os.getenv("GOOGLE_API_KEY")

# --- Initialize Extensions ---
db.init_app(app)
bcrypt = Bcrypt(app)
# Fix: Updated CORS configuration
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"], "supports_credentials": True}})
jwt = JWTManager(app)

# Initialize invoice processor
invoice_processor = InvoiceProcessor(api_key=GEMINI_API_KEY)

# --- Create Upload Folders ---
for folder in [app.config['UPLOAD_FOLDER'], app.config['AADHAR_FOLDER'], app.config['PAN_FOLDER'], app.config['INVOICE_FOLDER'], app.config['STATEMENT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Helper Functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the BFSI backend!"})

@app.route("/check-db")
def check_db():
    try:
        result = db.session.execute(text('SELECT 1')).fetchone()
        return jsonify({"status": "Database connected", "result": str(result[0])})
    except Exception as e:
        return jsonify({"status": "Database error", "error": str(e)}), 500

@app.route("/users")
def list_users():
    try:
        users = Users.query.all()
        user_list = [{"id": user.id, "name": user.name, "email": user.email, "phone": user.phone} for user in users]
        return jsonify({"count": len(user_list), "users": user_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Welcome to the BFSI backend!"})


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET": 
        return "This is the Signup API endpoint. Please POST your form here.", 200
    try:
        print("Signup request received")
        print("Content-Type:", request.headers.get('Content-Type'))
        
        # Get form data (multipart/form-data from frontend)
        name = request.form.get('name')
        dob = request.form.get('dob')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Use file data
        aadhar_file = request.files.get('aadhar')
        pan_file = request.files.get('pan')

        print("Signup request received")
        print(f"Name: {name}, Email: {email}, Phone: {phone}, DOB: {dob}")
        
        # Validate required fields
        if not all([name, dob, email, phone, password]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Check if user already exists
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email already exists"}), 409
        
        if not aadhar_file or not pan_file:
            return jsonify({"error": "Aadhar and PAN documents are required"}), 400
        
        # Validate file types
        if not allowed_file(aadhar_file.filename) or not allowed_file(pan_file.filename):
            return jsonify({"error": "Invalid file type. Allowed types: PDF, JPG, PNG"}), 400
            
        # Create unique filenames using timestamp + email
        timestamp = int(time.time())
        
        aadhar_filename = f"{timestamp}_{secure_filename(email)}_{secure_filename(aadhar_file.filename)}"
        pan_filename = f"{timestamp}_{secure_filename(email)}_{secure_filename(pan_file.filename)}"
        
        aadhar_path = os.path.join(AADHAR_FOLDER, aadhar_filename)
        pan_path = os.path.join(PAN_FOLDER, pan_filename)
        
        # Save files
        aadhar_file.save(aadhar_path)
        pan_file.save(pan_path)
        
        # Store relative paths in database
        db_aadhar_path = os.path.join('uploads/aadhar', aadhar_filename)
        db_pan_path = os.path.join('uploads/pan', pan_filename)

        # Verify documents using Gemini + email script
        result = verify_documents(db_aadhar_path, db_pan_path, email)
        print(result)

        if result["Status"] == "Rejected":
            return jsonify({"message": "Document verification failed!"}), 400
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Convert dob string to datetime
        dob_date = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None

        new_user = Users(
            name=name,
            dob=dob_date,
            email=email,
            phone=phone,
            password=hashed_password,
            aadhar_file=result['Aadhaar'],
            pan_file=result['PAN'],
            status=result["Status"],
        )
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        print(f"User created: ID={new_user.id}, email={new_user.email}")
        print("done")
        # Generate token - ENSURE we use user ID as identity
        access_token = create_access_token(identity=new_user.id)
        return jsonify({
            "token": access_token,
            "email": new_user.email,
            "name": new_user.name,
            "user_id": new_user.id,
            "message": "User created successfully"
        }), 201
        
    except Exception as e:
        print("Signup Error:", str(e))
        db.session.rollback()  # Roll back the session on error
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        print("Login request received")
        
        # Handle different content types
        if request.headers.get('Content-Type') == 'application/json':
            data = request.get_json(force=True)
        else:
            data = request.form
        
        email = data.get("email")
        password = data.get("password")
        
        print(f"Login attempt: email={email}")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        user = Users.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # ENSURE we use user ID as identity for JWT token
            token = create_access_token(identity=user.id)
            return jsonify({
                "token": token, 
                "email": user.email,
                "name": user.name,
                "user_id": user.id,  # Add user_id to response for consistency
                "message": "Login successful"
            })
        
        return jsonify({"error": "Invalid credentials"}), 401
    
    except Exception as e:
        print("Login Error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        # Get email from request query parameters or default to a test user
        email = request.args.get('email')
        
        # If no email provided, return a default response
        if not email:
            return jsonify({
                "message": "Welcome Guest User!",
                "user_id": 0,
                "email": "guest@example.com",
                "name": "Guest User",
                "phone": "Not provided"
            })
            
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                "message": "Welcome Guest User!",
                "user_id": 0,
                "email": email,
                "name": "Guest User",
                "phone": "Not provided"
            })
         
        return jsonify({
            "message": f"Welcome {user.name}!",
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone
        })
    
    except Exception as e:
        print("Dashboard Error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/upload-invoice', methods=['POST'])
def upload_invoice():
    # Get user_id from form or query parameters, default to 1 if not provided
    user = request.form.get('user_id', request.args.get('user_id', 1, type=int))
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if not file.filename.split('.')[-1].lower() in allowed_extensions:
        return jsonify({'error': 'File type not allowed. Please upload PDF, JPG, JPEG, or PNG.'}), 400

    try:
        # Save the file
        timestamp = int(time.time())
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config['INVOICE_FOLDER'], filename)
        file.save(file_path)

        # Process the invoice with our invoice processor
        extracted_data = invoice_processor.process_invoice(file_path)
        
        # Extract JSON from the response text
        json_data = invoice_processor.extract_json_from_ai_response(extracted_data)
        
        # Check for errors
        if "error" in json_data:
            return jsonify({"error": json_data["error"]}), 500
            
        # Convert the json_data to a string for storage
        extracted_json_str = json.dumps(json_data)
        
        # Save file info to InvoiceData model
        invoice_data_entry = InvoiceData(
            # user_id=user.id,
            file_name=file.filename,
            file_path=file_path,
            extracted_data=extracted_json_str
        )
        db.session.add(invoice_data_entry)
        db.session.commit()
        
        # Parse extracted data for structured storage
        parsed_data = invoice_processor.parse_invoice_data(json_data)
        
        # Store extracted structured invoice data in the Invoice model
        try:
            invoice_record = Invoice(
                user_id=user.id,
                invoice_number=parsed_data["invoice_number"],
                vendor_details=parsed_data["vendor_details"],
                date=parsed_data["date"],
                total_amount=parsed_data["total_amount"],
                tax_amount=parsed_data["tax_amount"],
                subtotal_amount=parsed_data["subtotal_amount"],
                category=parsed_data["category"],
                classification_confidence=parsed_data["classification_confidence"],
                line_items=json.dumps(parsed_data["line_items"])
            )
            db.session.add(invoice_record)
            db.session.commit()
            invoice_id = invoice_record.id
        except Exception as e:
            invoice_id = None
            print(f"Error creating Invoice record: {str(e)}")

        response_data = {
            "message": "File uploaded and processed successfully",
            "file_name": file.filename,
            "file_path": file_path,
            "extracted_data": json_data,
            "invoice_id": invoice_id,
            "status": "success"
        }
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error processing invoice: {str(e)}")
        return jsonify({"error": f"Error processing invoice: {str(e)}"}), 500



@app.route('/upload-statement', methods=['POST'])
def upload_statement():
    # Get user_id from form or query parameters, default to 1 if not provided
    user_id = request.form.get('user_id', request.args.get('user_id', 1, type=int))
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if not file.filename.split('.')[-1].lower() in allowed_extensions:
        return jsonify({'error': 'File type not allowed. Please upload PDF, JPG, JPEG, or PNG.'}), 400
    
    try:
        # Save the file
        timestamp = int(time.time())
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config['STATEMENT_FOLDER'], filename)
        file.save(file_path)
        
        # Process the statement file
        combined_text = ""
        
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            img = Image.open(file_path)
            combined_text += extract_text_from_image(img)
        else:
            combined_text += get_pdf_text([file_path])

        # Create text chunks and store them in vector database
        text_chunks = get_text_chunks(combined_text)
        get_vector_store(text_chunks)
        
        return jsonify({
            "message": "Statement uploaded and processed successfully", 
            "status": "success",
            "file_name": filename,
            "info": "You can now ask questions about this statement"
        }), 200
    except Exception as e:
        print(f"Error processing statement: {str(e)}")
        return jsonify({"error": f"Error processing statement: {str(e)}"}), 500

@app.route('/ask-question', methods=['POST'])
def ask():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No question provided. Please send a JSON with 'question' field."}), 400
            
        user_question = data.get('question')
        if not user_question:
            return jsonify({"error": "Question field is empty"}), 400
            
        # Process the question using LangChain
        response_text = user_input(user_question)
        
        return jsonify({
            "answer": response_text,
            "status": "success"
        }), 200
    except Exception as e:
        print(f"Error processing question: {str(e)}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 500




# --- Initialize DB ---
with app.app_context():
    db.create_all()

# --- Run App (Optional for development) ---
if __name__ == '__main__':
    app.run(debug=True)