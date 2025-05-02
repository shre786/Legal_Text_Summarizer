import os
import uuid
import mysql.connector
from PyPDF2 import PdfReader
from utils.auth import connect_db

UPLOAD_FOLDER = "data/user_data"

def save_uploaded_file(file, username):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file_id}.pdf")

    with open(file_path, "wb") as f:
        f.write(file.read())

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO uploads (username, filename, file_path) VALUES (%s, %s, %s)", 
                   (username, file.filename, file_path))
    db.commit()
    db.close()

    return file_path

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        return text.strip() if text else "Error: No readable text found in the PDF."
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def save_summary(username, filename, summary):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE uploads SET summary = %s WHERE username = %s AND filename = %s", 
                   (summary, username, filename))
    db.commit()
    db.close()

def get_user_files(username):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, filename, file_path, upload_date, summary FROM uploads WHERE username = %s ORDER BY upload_date DESC", (username,))
    files = cursor.fetchall()
    db.close()
    return files

def get_case_text(username, filename):
    """Retrieve the case text from the database for chatbot reference."""
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT summary FROM uploads WHERE username=%s AND filename=%s", (username, filename))
    result = cursor.fetchone()
    db.close()
    return result[0] if result else None
