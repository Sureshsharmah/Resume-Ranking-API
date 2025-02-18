from fastapi import FastAPI, File, UploadFile, HTTPException, Form
import openai
from pypdf import PdfReader
from docx import Document
import io
import pandas as pd
from fastapi.responses import FileResponse
import json
import logging
from typing import List, Dict

# Initialize FastAPI app
app = FastAPI(
    title="Resume Ranking API",
    description="Automates the ranking of resumes based on job descriptions.",
    version="1.0"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF files."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(docx_bytes):
    """Extract text from DOCX files."""
    try:
        doc = Document(io.BytesIO(docx_bytes))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")

def extract_criteria_from_job_description(job_description_text):
    """Extract key ranking criteria from a job description using OpenAI."""
    prompt = f"""
    Extract the key ranking criteria from the following job description:
    {job_description_text}
    Return a JSON array of key ranking criteria such as skills, experience, and certifications.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        criteria = json.loads(response["choices"][0]["message"]["content"])
        return {"criteria": criteria}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

def analyze_resume(resume_text, criteria):
    """Analyze a resume based on extracted job criteria using OpenAI."""
    prompt = f"""
    Evaluate the following resume based on these ranking criteria:
    {criteria}
    Resume:
    {resume_text}
    Return a JSON object with the candidate's name and scores for each criterion on a scale of 0 to 5.
    Example:
    {{
      "Candidate Name": "John Doe",
      "scores": {{
        "Experience": 4,
        "Certifications": 5,
        "Python": 5,
        "SQL": 4,
        "Machine Learning": 3,
        "Deep Learning": 2,
        "NLP": 1,
        "Gen AI": 0
      }}
    }}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        evaluation = json.loads(response["choices"][0]["message"]["content"])
        logger.info(f"Evaluation: {evaluation}")
        return evaluation
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        # Return default scores if OpenAI API fails
        return {
            "Candidate Name": "Unknown",
            "scores": {
                "Experience": 0,
                "Certifications": 0,
                "Python": 0,
                "SQL": 0,
                "Machine Learning": 0,
                "Deep Learning": 0,
                "NLP": 0,
                "Gen AI": 0
            }
        }

def save_evaluation_to_excel(evaluation_data: List[Dict]):
    """Save the structured resume evaluation data to an Excel file with proper formatting."""
    
    # Define the desired columns
    desired_columns = [
        "Candidate Name",
        "Experience",
        "Certifications",
        "Python",
        "SQL",
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Gen AI",
        "Total Score"
    ]
    
    structured_data = []
    
    for entry in evaluation_data:
        candidate_name = entry.get("Candidate Name", "Unknown")
        scores = entry.get("scores", {})

        # Create a formatted entry with the desired columns
        formatted_entry = {
            "Candidate Name": candidate_name,
            "Experience": scores.get("Experience", 0),
            "Certifications": scores.get("Certifications", 0),
            "Python": scores.get("Python", 0),
            "SQL": scores.get("SQL", 0),
            "Machine Learning": scores.get("Machine Learning", 0),
            "Deep Learning": scores.get("Deep Learning", 0),
            "NLP": scores.get("NLP", 0),
            "Gen AI": scores.get("Gen AI", 0),
            "Total Score": sum(scores.values())  # Calculate total score
        }
        structured_data.append(formatted_entry)

    # Convert structured data into a DataFrame
    df = pd.DataFrame(structured_data, columns=desired_columns)

    # Save as Excel file
    excel_filename = "evaluation_results.xlsx"
    df.to_excel(excel_filename, index=False)

    return excel_filename

@app.post("/extract-criteria")
async def extract_criteria(file: UploadFile = File(...)):
    """Extract key ranking criteria from a job description (PDF/DOCX)."""
    
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are supported.")
    
    file_bytes = await file.read()
    text = extract_text_from_pdf(file_bytes) if file.content_type == "application/pdf" else extract_text_from_docx(file_bytes)
    
    return extract_criteria_from_job_description(text)

@app.post("/score-resumes")
async def score_resumes(
    criteria: str = Form(...),  # Accepts a JSON string of criteria
    files: List[UploadFile] = File(...)
):
    """Score resumes against extracted ranking criteria and return results as an Excel file."""
    
    try:
        # Convert criteria string to a Python list
        criteria_list = json.loads(criteria)
        logger.info(f"Parsed criteria: {criteria_list}")

        evaluation_data = []

        for file in files:
            if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are supported.")
            
            file_bytes = await file.read()
            resume_text = extract_text_from_pdf(file_bytes) if file.content_type == "application/pdf" else extract_text_from_docx(file_bytes)
            logger.info(f"Extracted text from {file.filename}")

            evaluation = analyze_resume(resume_text, criteria_list)
            logger.info(f"Evaluation for {file.filename}: {evaluation}")
            evaluation_data.append(evaluation)

        # Save results in a structured format
        excel_file = save_evaluation_to_excel(evaluation_data)
        logger.info(f"Excel file generated: {excel_file}")

        return FileResponse(excel_file, filename=excel_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid criteria format. Ensure it's a valid JSON array.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")