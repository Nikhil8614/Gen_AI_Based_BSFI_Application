import React, { useEffect, useState } from "react";
import axios from "axios";

function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("No file selected");
  const [processingInvoice, setProcessingInvoice] = useState(false);
  const [invoiceResponse, setInvoiceResponse] = useState(null);
  const [invoiceError, setInvoiceError] = useState(null);
  const [activeTab, setActiveTab] = useState("invoice"); // Add state for active tab
  const [statementQuestion, setStatementQuestion] = useState(""); // Add state for statement question
  const [statementResponse, setStatementResponse] = useState(null); // Add state for statement analysis response
  const [processingStatement, setProcessingStatement] = useState(false); // Add state for statement processing status
  const [statementError, setStatementError] = useState(null);
  const [statementUploaded, setStatementUploaded] = useState(false);
  const [askingQuestion, setAskingQuestion] = useState(false);
  // Get token from localStorage
  const token = localStorage.getItem('accessToken');

  // Fetch user data on component mount
  useEffect(() => {
    if (!token) {
      setError("No authentication token found. Please login.");
      setLoading(false);
      return;
    }

    const fetchUserData = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/dashboard', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        setUserData(response.data);
      } catch (err) {
        console.error("Error fetching user data:", err);
        setError("Failed to load user data. Please try logging in again.");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [token]);

  // Handle file selection
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFilename(selectedFile.name);
    } else {
      setFile(null);
      setFilename("No file selected");
    }
  };

  // Handle file upload
  const handleUploadInvoice = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    setProcessingInvoice(true);
    setInvoiceError(null);
    setInvoiceResponse(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:5000/upload-invoice",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            "Authorization": `Bearer ${token}`
          }
        }
      );

      console.log("Response received:", res.data);
      setInvoiceResponse(res.data);
      
      // Clear file input after successful upload
      setFile(null);
      setFilename("No file selected");
      
    } catch (error) {
      console.error("Error uploading file:", error);
      
      if (error.response) {
        // Get more detailed error message if available
        const errorMessage = error.response.data.error || error.response.data.message || error.response.statusText;
        setInvoiceError(`Server error: ${errorMessage}`);
      } else if (error.request) {
        setInvoiceError("No response from server. Please check your connection.");
      } else {
        setInvoiceError(`Error: ${error.message}`);
      }
    } finally {
      setProcessingInvoice(false);
    }
  };


   const handleUploadStatement = async () => {
  if (!file) {
    alert("Please select a statement file first!");
    return;
  }

  setProcessingStatement(true);
  setStatementError(null);
  setStatementResponse(null);
  
  const formData = new FormData();
  formData.append("file", file);
  if (userData && userData.user_id) {
    formData.append("user_id", userData.user_id);
  }

  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/upload-statement",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
          "Authorization": `Bearer ${token}`
        }
      }
    );

    console.log("Statement upload response:", res.data);
    setStatementUploaded(true);
    setStatementResponse({
      message: res.data.message || "Statement uploaded successfully. You can now ask questions about it."
    });
    
    // Clear file input after successful upload
    setFile(null);
    setFilename("No file selected");
    
  } catch (error) {
    console.error("Error uploading statement:", error);
    
    if (error.response) {
      const errorMessage = error.response.data.error || error.response.data.message || error.response.statusText;
      setStatementError(`Server error: ${errorMessage}`);
    } else if (error.request) {
      setStatementError("No response from server. Please check your connection.");
    } else {
      setStatementError(`Error: ${error.message}`);
    }
    setStatementUploaded(false);
  } finally {
    setProcessingStatement(false);
  }
};

const handleAskQuestion = async () => {
  if (!statementQuestion.trim()) {
    alert("Please enter a question about the statement!");
    return;
  }

  setAskingQuestion(true);
  setStatementError(null);

  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/ask-question",
      { question: statementQuestion },
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        }
      }
    );

    console.log("Question response:", res.data);
    setStatementResponse({
      ...statementResponse,
      answer: res.data.answer
    });
    
  } catch (error) {
    console.error("Error asking question:", error);
    
    if (error.response) {
      const errorMessage = error.response.data.error || error.response.data.message || error.response.statusText;
      setStatementError(`Server error: ${errorMessage}`);
    } else if (error.request) {
      setStatementError("No response from server. Please check your connection.");
    } else {
      setStatementError(`Error: ${error.message}`);
    }
  } finally {
    setAskingQuestion(false);
  }
};
 
  // Process vendor details to handle both string and object types
  const processVendorDetails = (vendorDetails) => {
    if (!vendorDetails) return "Unknown Vendor";
    
    // If it's already a string, return it
    if (typeof vendorDetails === 'string') return vendorDetails;
    
    // If vendor_details_str is available, use it
    if (typeof vendorDetails === 'object' && 'vendor_details_str' in vendorDetails) {
      return vendorDetails.vendor_details_str;
    }
    
    // If it's an object, convert it to a readable string
    if (typeof vendorDetails === 'object') {
      try {
        const parts = [];
        for (const [key, value] of Object.entries(vendorDetails)) {
          if (value) {
            parts.push(`${key.replace('_', ' ')}: ${value}`);
          }
        }
        return parts.join(', ');
      } catch (e) {
        console.error("Error formatting vendor details:", e);
        return JSON.stringify(vendorDetails);
      }
    }
    
    // Fallback
    return String(vendorDetails);
  };

  const formatInvoiceData = (data) => {
    if (!data || !data.extracted_data) return null;
    
    const extractedData = data.extracted_data;
    
    // Define the fields we want to display and their labels
    const fieldDefinitions = [
      { key: 'invoice_number', label: 'Invoice Number' },
      { 
        key: 'vendor_details', 
        label: 'Vendor',
        format: value => processVendorDetails(value)
      },
      { key: 'date', label: 'Date' },
      { key: 'total_amount', label: 'Total Amount', format: value => value ? `₹${parseFloat(value).toFixed(2)}` : 'N/A' },
      { key: 'tax_amount', label: 'Tax', format: value => value ? `₹${parseFloat(value).toFixed(2)}` : 'N/A' },
      { key: 'subtotal_amount', label: 'Subtotal', format: value => value ? `₹${parseFloat(value).toFixed(2)}` : 'N/A' },
      { key: 'classification_confidence', label: 'Classification Confidence', format: value => value ? `${(parseFloat(value) * 100).toFixed(1)}%` : 'N/A' }
    ];

    return (
      <div className="invoice-data">
        <ul className="invoice-details-list">
          {fieldDefinitions.map(field => {
            if (extractedData[field.key] !== undefined) {
              const displayValue = field.format ? 
                field.format(extractedData[field.key]) : 
                extractedData[field.key];
              
              return (
                <li key={field.key} className="invoice-detail-item">
                  <span className="detail-label">{field.label}:</span>
                  <span className="detail-value">{displayValue}</span>
                </li>
              );
            }
            return null;
          })}
        </ul>

        {/* Display line items if available */}
        {extractedData.line_items && extractedData.line_items.length > 0 && (
          <div className="line-items-section">
            <h4 className="section-title">Line Items:</h4>
            <ul className="line-items-list">
              {extractedData.line_items.map((item, index) => (
                <li key={index} className="line-item">
                  <div className="line-item-details">
                    <span className="item-description">{item.description}</span>
                    <span className="item-quantity">Qty: {item.quantity || 1}</span>
                    <span className="item-unit-price">Unit: ₹{parseFloat(item.unit_price || 0).toFixed(2)}</span>
                    <span className="item-total-price">Total: ₹{parseFloat(item.total_price || 0).toFixed(2)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Loading user data...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!userData) {
    return <div className="error-message">User information not available. Please log in again.</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="user-profile-section">
        <h2>Welcome, {userData.name || userData.email}</h2>
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'invoice' ? 'active' : ''}`}
            onClick={() => setActiveTab('invoice')}
          >
            INVOICE PROCESSOR
          </button>
          <button 
            className={`tab-button ${activeTab === 'statement' ? 'active' : ''}`}
            onClick={() => setActiveTab('statement')}
          >
            STATEMENT ANALYSIS
          </button>
        </div>
      </div>

      {activeTab === 'invoice' ? (
        <div className="invoice-upload-section">
          <h3>Upload Invoice for AI Analysis</h3>
          <p className="upload-description">
            Upload your invoice (PDF, JPG, JPEG, or PNG) to have our AI analyze and categorize it.
          </p>
          
          <div className="file-upload-container">
            <div className="file-input-wrapper">
              <input 
                type="file" 
                className="file-input"
                onChange={handleFileChange} 
                accept=".pdf,.jpg,.jpeg,.png" 
              />
              <p className="selected-filename">{filename}</p>
            </div>
            
            <button 
              className="upload-button" 
              onClick={handleUploadInvoice}
              disabled={processingInvoice || !file}
            >
              {processingInvoice ? "Processing..." : "Upload Invoice"}
            </button>
          </div>
          
          {processingInvoice && (
            <div className="processing-message">
              <p>Processing your invoice. This may take a few moments...</p>
            </div>
          )}
          
          {invoiceError && (
            <div className="error-message">
              <p>{invoiceError}</p>
            </div>
          )}
          
          {invoiceResponse && (
            <div className="response-container">
              <div className="response-header">
                <h3 className="response-title">Invoice Analysis Results</h3>
                <span className={`response-status ${invoiceResponse.status !== "success" ? "error" : "success"}`}>
                  {invoiceResponse.status === "success" ? "✓ Success" : "× Failed"}
                </span>
              </div>
              
              {invoiceResponse.extracted_data && (
                <div className="file-info">
                  <div className="file-header">
                    <p><strong>File:</strong> {invoiceResponse.file_name}</p>
                    {invoiceResponse.invoice_id && (
                      <p><strong>Invoice ID:</strong> {invoiceResponse.invoice_id}</p>
                    )}
                  </div>
                  
                  {invoiceResponse.extracted_data.category && (
                    <div className="category-badge">
                      <span><strong>Category: </strong>{invoiceResponse.extracted_data.category}</span>
                    </div>
                  )}
                </div>
              )}
              
              <h4 className="data-section-title">Extracted Invoice Data:</h4>
              <div className="data-display">
                {formatInvoiceData(invoiceResponse)}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="statement-upload-section">
  <h3>Upload Statement for AI Analysis</h3>
  <p className="upload-description">
    Upload your statement (PDF, JPG, JPEG, or PNG) and ask questions to get AI-powered insights.
  </p>
  
  {!statementUploaded ? (
    // Statement Upload Phase
    <div className="file-upload-container">
      <div className="file-input-wrapper">
        <input 
          type="file" 
          className="file-input"
          onChange={handleFileChange} 
          accept=".pdf,.jpg,.jpeg,.png" 
        />
        <p className="selected-filename">{filename}</p>
      </div>
      
      <button 
        className="upload-button"
        onClick={handleUploadStatement}
        disabled={processingStatement || !file}
      >
        {processingStatement ? "Processing..." : "Upload Statement"}
      </button>
    </div>
  ) : (
    // Question Phase - Only shown after successful upload
    <div className="statement-question-container">
      <p className="statement-upload-success">
        Statement processed successfully! Ask questions about your statement below.
      </p>
      <textarea
        className="statement-question-input"
        placeholder="Ask a question about the statement..."
        value={statementQuestion}
        onChange={(e) => setStatementQuestion(e.target.value)}
        rows={3}
      />
      <button 
        className="ask-button"
        onClick={handleAskQuestion}
        disabled={askingQuestion || !statementQuestion.trim()}
      >
        {askingQuestion ? "Getting Answer..." : "Get Answer"}
      </button>
    </div>
  )}
  
  {processingStatement && (
    <div className="processing-message">
      <p>Processing your statement. This may take a few moments...</p>
    </div>
  )}
  
  {askingQuestion && (
    <div className="processing-message">
      <p>Finding answer to your question...</p>
    </div>
  )}
  
  {statementError && (
    <div className="error-message">
      <p>{statementError}</p>
    </div>
  )}
  
  {statementResponse && (
    <div className="response-container">
      <div className="response-header">
        <h3 className="response-title">Statement Analysis</h3>
        <span className="response-status success">
          ✓ {statementUploaded ? "Statement Processed" : ""}
        </span>
      </div>
      
      {statementResponse.message && (
        <div className="statement-message">
          <p>{statementResponse.message}</p>
        </div>
      )}
      
      {statementResponse.answer && (
        <div className="statement-response">
          <div className="statement-question-display">
            <strong>Your Question:</strong>
            <p>{statementQuestion}</p>
          </div>
          <div className="statement-answer">
            <strong>AI Answer:</strong>
            <p className="ai-response-text">{statementResponse.answer}</p>
          </div>
        </div>
      )}
    </div>
  )}
</div>
      )}
    </div>
  );
} 

export default Dashboard;
