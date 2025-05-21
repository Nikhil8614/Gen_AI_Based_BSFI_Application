from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
import pdfplumber
import pytesseract
from PIL import Image
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def get_pdf_text(pdf_paths):
    text = ""
    for pdf_path in pdf_paths:
        with pdfplumber.open(pdf_path) as pdf_reader:
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    # If no text, OCR the page as image
                    page_image = page.to_image()
                    ocr_text = extract_text_from_image(page_image.original)
                    text += ocr_text
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    You are an intelligent financial assistant specialized in analyzing bank statements. Use the provided context to answer the user's question as accurately and concisely as possible, while including all relevant details. If appropriate, also offer clear and responsible financial advice based on spending patterns.

Context:
{context}

Question:
{question}

Answer Guidelines:
1. If the answer is present in the context:
   - Provide a concise, informative response.
   - If the question is about transactions, identify key insights like highest or lowest transactions.
   - If the question is about savings, suggest practical tips such as reducing spending on luxury or discretionary items.
   - Recommend safe and traditional saving options (e.g., fixed deposits, gold savings, emergency funds), but **do NOT suggest crypto, stocks, or unregulated investments**.
   - For generic financial health queries, tailor advice based on context (e.g., overspending on dining, subscriptions, etc.).

2. If the answer is NOT in the context:
   - Respond with: "The answer is not in the provided context. However, here is some general information that may help:"
   - Provide relevant financial insights if possible.
   - Suggest related financial topics or questions.
   - Encourage the user to ask another question if they need further assistance.

Examples of Additional Tips to Include (when context allows):
- "Consider reducing frequent expenses such as food delivery or online shopping."
- "You may benefit from setting up a monthly budget and tracking categories like entertainment and utilities."
- "Investing in traditional options like gold or fixed deposits can be safer long-term strategies."

If possible, always summarize:
- The **highest transaction** (amount and description).
- The **lowest transaction** (amount and description).
- The **total amount spent** in the last month.
"""
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    """
    Process user questions by searching the vector database for relevant context
    and using that context to generate an answer.
    
    Args:
        user_question (str): The question from the user about the statement
        
    Returns:
        str: The AI-generated answer to the user's question
    """
    try:
        # Load vector store with embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Try to load the local FAISS index
        try:
            new_db = FAISS.load_local("faiss_index", embeddings)
            # Search for similar documents
            docs = new_db.similarity_search(user_question)
            # Get the conversational chain
            chain = get_conversational_chain()
            # Generate a response using the chain with the retrieved documents
            response = chain.invoke({"input_documents": docs, "question": user_question})
            return response["output_text"]
        except Exception as e:
            # If FAISS index loading fails, handle gracefully
            print(f"Error loading FAISS index: {str(e)}")
            return "I couldn't find information about that in your statement. Please try uploading your statement again or asking a different question."
            
    except Exception as e:
        print(f"Error in user_input: {str(e)}")
        return f"I'm having difficulty processing your question: {str(e)}"