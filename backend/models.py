# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.BigInteger, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    aadhar_file = db.Column(db.String(50), nullable=False)  # Path to stored Aadhar file
    pan_file = db.Column(db.String(255), nullable=False)     # Path to stored PAN file
    status = db.Column(db.Enum('pending', 'rejected', 'verified', name='status_enum'),default='pending',nullable=False)
    uploaded_time = db.Column(db.DateTime,default=db.func.current_timestamp(),nullable=False)
    
    def __repr__(self):
        return f'<Users {self.email}>'
    
class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invoice_number = db.Column(db.String(50))
    vendor_details = db.Column(db.Text)
    date = db.Column(db.String(20))
    total_amount = db.Column(db.Float)
    tax_amount = db.Column(db.Float)
    subtotal_amount = db.Column(db.Float)
    category = db.Column(db.String(100))
    classification_confidence = db.Column(db.Float)
    line_items = db.Column(db.Text)
    
    # Add relationship if needed
    user = db.relationship('Users', backref='invoices')

class InvoiceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    extracted_data = db.Column(db.Text)  # Can store any string/JSON
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InvoiceData {self.file_name}>'


