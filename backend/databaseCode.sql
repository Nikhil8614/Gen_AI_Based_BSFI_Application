-- Create the database
CREATE DATABASE invoice_processor;
-- Use the database
USE invoice_processor;
-- Create the users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(200) NOT NULL,
    aadhar VARCHAR(255) NOT NULL, 
    pan VARCHAR(255) NOT NULL,
    status ENUM('Pending','Verified','Rejected') DEFAULT 'Pending',
    enrolled_time TIMESTAMP DEFAULT current_timestamp
);

USE invoice_processor;
CREATE TABLE IF NOT EXISTS invoice_data(
	id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    extracted_data TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT current_timestamp
);