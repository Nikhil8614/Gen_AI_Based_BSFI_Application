import io
import json
from pathlib import Path
import google.generativeai as genai
import PyPDF2

class InvoiceProcessor:
    # List of valid invoice categories
    INVOICE_CATEGORIES = [
        "Food & Beverages",
        "Clothing & Apparel",
        "Healthcare",
        "Pharmacy & Medical Supplies",
        "Electronics & Technology",
        "Office Supplies",
        "Transportation",
        "Utilities",
        "Professional Services",
        "Entertainment",
        "Accommodation",
        "Construction & Maintenance",
        "Education & Training",
        "Marketing & Advertising",
        "Other"
    ]
    
    def __init__(self, api_key):
        """Initialize the InvoiceProcessor with Google API key."""
        # Configure Google Gemini AI
        genai.configure(api_key=api_key)
        
        # Model configuration
        self.model_config = {
            "temperature": 0.2,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 4096,
        }
        
        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.model_config,
            safety_settings=self.safety_settings
        )

    def process_invoice(self, file_path):
        """
        Process the uploaded file (PDF/Image) with Gemini AI to extract invoice data.
        
        Args:
            file_path: Path to the invoice file (PDF, JPG, JPEG, PNG)
            
        Returns:
            List of response texts from AI processing
        """
        system_prompt = """
        You are an AI specialized in invoice data extraction and classification.
        Your task is to analyze invoices from images or PDFs and return the extracted data in structured JSON format.

        Ensure the output contains:
        - Invoice Number
        - Vendor Details
        - Date
        - Amount (Total, Tax, Subtotal)
        - Line Items (list of items with description, quantity, unit price, and total price)
        - Category (classify the invoice into one of these categories: Food & Beverages, Clothing & Apparel, Healthcare, Pharmacy & Medical Supplies, Electronics & Technology, Office Supplies, Transportation, Utilities, Professional Services, Entertainment, Accommodation, Construction & Maintenance, Education & Training, Marketing & Advertising, Other)
        
        Return the data in valid JSON format with these keys:
        - invoice_number
        - vendor_details
        - date (in YYYY-MM-DD format)
        - total_amount (numeric)
        - tax_amount (numeric)
        - subtotal_amount (numeric)
        - line_items (array of objects with description, quantity, unit_price, and total_price)
        - category (one of the categories listed above)
        - classification_confidence (a value between 0 and 1 indicating confidence in the category classification)
        """

        user_prompt = "Extract and format the invoice data as JSON. Ensure the output is valid JSON format with all the required fields including the category classification and line items."

        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext in [".jpg", ".jpeg", ".png"]:
                image_info = [{"mime_type": "image/png", "data": Path(file_path).read_bytes()}]
            elif file_ext == ".pdf":
                # Try multiple approaches for PDF processing
                image_info = []
                # Send the PDF directly to Gemini
                try:
                    with open(file_path, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                    # Validate PDF before sending
                    try:
                        PyPDF2.PdfReader(io.BytesIO(pdf_data))
                        image_info.append({"mime_type": "application/pdf", "data": pdf_data})
                    except Exception as pdf_error:
                        raise Exception(f"Invalid PDF file: {str(pdf_error)}")
                except Exception as e:
                    # If all methods fail, return detailed error
                    error_msg = f"PDF processing failed: {str(e)}"
                    raise Exception(error_msg)           
            else:
                return [json.dumps({"error": "Unsupported file format"})]

            if not image_info:
                return [json.dumps({"error": "No images could be processed from the file"})]

            response_texts = []
            for img_data in image_info:
                input_prompt = [system_prompt, img_data, user_prompt]
                response = self.model.generate_content(input_prompt)
                response_texts.append(response.text)
                # For efficiency, just process the first page
                break

            return response_texts
        except Exception as e:
            print(f"Error in processing invoice: {str(e)}")
            return [json.dumps({"error": f"Error processing file: {str(e)}"})]
    
    @staticmethod
    def extract_json_from_ai_response(extracted_data):
        """
        Extract JSON from the AI response text.
        
        Args:
            extracted_data: List of response texts from AI processing
            
        Returns:
            Dictionary containing the extracted JSON data or error message
        """
        for text in extracted_data:
            # Check if the response contains an error
            try:
                potential_error = json.loads(text)
                if "error" in potential_error:
                    return {"error": potential_error["error"]}
            except:
                pass

            # Look for JSON content in the response
            text = text.strip()
            # Find the first { and last } to extract JSON
            if '{' in text and '}' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                potential_json = text[start:end]
                
                try:
                    json_data = json.loads(potential_json)
                    return json_data
                except json.JSONDecodeError:
                    # Try to clean up the JSON string if needed
                    cleaned_json = potential_json.replace('\n', ' ').replace('\r', '')
                    try:
                        json_data = json.loads(cleaned_json)
                        return json_data
                    except:
                        continue

        return {"error": "Could not extract valid JSON from AI response"}
    
    @staticmethod
    def parse_invoice_data(json_data):
        """
        Parse and normalize extracted invoice data.
        
        Args:
            json_data: Raw JSON data from AI processing
            
        Returns:
            Dictionary with normalized invoice data
        """
        # Parse extracted data for structured storage
        invoice_number = json_data.get("invoice_number", "Unknown")
        vendor_details = json_data.get("vendor_details", "Unknown Vendor")
        date_str = json_data.get("date", None)
        
        # Normalize numeric fields
        # Total amount
        total_amount = json_data.get("total_amount", 0.0)
        if isinstance(total_amount, str):
            # Remove currency symbols and commas
            total_amount = total_amount.replace('$', '').replace(',', '')
            try:
                total_amount = float(total_amount)
            except ValueError:
                total_amount = 0.0
        
        # Tax amount
        tax_amount = json_data.get("tax_amount", 0.0)
        if isinstance(tax_amount, str):
            tax_amount = tax_amount.replace('$', '').replace(',', '')
            try:
                tax_amount = float(tax_amount)
            except ValueError:
                tax_amount = 0.0
        
        # Subtotal amount
        subtotal_amount = json_data.get("subtotal_amount", 0.0)
        if isinstance(subtotal_amount, str):
            subtotal_amount = subtotal_amount.replace('$', '').replace(',', '')
            try:
                subtotal_amount = float(subtotal_amount)
            except ValueError:
                subtotal_amount = 0.0
        
        # Category and confidence
        category = json_data.get("category", "Other")
        # Ensure category is one of the predefined categories
        if category not in InvoiceProcessor.INVOICE_CATEGORIES:
            category = "Other"
        
        classification_confidence = json_data.get("classification_confidence", 0.0)
        if isinstance(classification_confidence, str):
            try:
                classification_confidence = float(classification_confidence)
            except ValueError:
                classification_confidence = 0.0
        
        # Process line items
        line_items = json_data.get("line_items", [])
        if not isinstance(line_items, list):
            line_items = []
        
        # Format line items properly
        formatted_line_items = []
        for item in line_items:
            formatted_item = {}
            if isinstance(item, dict):
                formatted_item["description"] = item.get("description", "")
                
                # Process quantity
                quantity = item.get("quantity", 0)
                if isinstance(quantity, str):
                    try:
                        quantity = float(quantity)
                    except ValueError:
                        quantity = 0
                formatted_item["quantity"] = quantity
                
                # Process unit_price
                unit_price = item.get("unit_price", 0)
                if isinstance(unit_price, str):
                    unit_price = unit_price.replace('$', '').replace(',', '')
                    try:
                        unit_price = float(unit_price)
                    except ValueError:
                        unit_price = 0
                formatted_item["unit_price"] = unit_price
                
                # Process total_price
                total_price = item.get("total_price", 0)
                if isinstance(total_price, str):
                    total_price = total_price.replace('$', '').replace(',', '')
                    try:
                        total_price = float(total_price)
                    except ValueError:
                        total_price = 0
                formatted_item["total_price"] = total_price
                
                formatted_line_items.append(formatted_item)
        
        # Return normalized data
        return {
            "invoice_number": invoice_number,
            "vendor_details": vendor_details,
            "date": date_str,
            "total_amount": total_amount,
            "tax_amount": tax_amount,
            "subtotal_amount": subtotal_amount,
            "category": category,
            "classification_confidence": classification_confidence,
            "line_items": formatted_line_items
        }