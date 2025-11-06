"""
PDF processing module for extracting text from medical reports.
"""

import os
import PyPDF2


def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content, or None if extraction fails
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Error: PDF file not found at {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            if reader.is_encrypted:
                print(f"Warning: PDF {pdf_path} is encrypted. Unable to extract text.")
                return None

            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip() if text else None
            
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None
