from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from utils.auth import register_user, authenticate_user, connect_db
from utils.file_handling import save_uploaded_file, get_user_files, extract_text_from_pdf, save_summary, get_case_text
from models.summarization import summarize_text
from chat import get_relevant_info
from evluate import evaluate_summary

app = Flask(__name__, template_folder="templates")
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials. Try again."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        address = request.form['address']
        occupation = request.form['occupation']

        if register_user(username, password, name, surname, email, address, occupation):
            return redirect(url_for('login'))
        else:
            return "Username already exists."
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_files = get_user_files(username)
    
    summary = None
    summary_filename = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        
        filename = secure_filename(file.filename)
        file_path = save_uploaded_file(file, username)
        
        text = extract_text_from_pdf(file_path)
        raw_summary = summarize_text(text)
        
        summary = f"""
        <h2>Case Summary</h2>
        <ul>
            🟢 <b>Parties Involved:</b> {raw_summary.get('Parties Involved', 'Not specified')}<br>
            🔵 <b>Case Laws Referenced:</b> {raw_summary.get('Case Laws Referenced', 'Not specified')}<br>
            🟠 <b>Jurisdiction:</b> {raw_summary.get('Jurisdiction', 'Not specified')}<br>
            🟣 <b>Key Points:</b> {raw_summary.get('Key Points', 'Not available')}<br>
        </ul>
        """

        save_summary(username, filename, summary)
        summary_filename = filename
    
    return render_template('dashboard.html', summary=summary, user_files=user_files, summary_filename=summary_filename)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    user_question = data.get("question")
    filename = data.get("filename")
    username = session['username']

    case_text = get_case_text(username, filename)
    if not case_text:
        return jsonify({"response": "No relevant case document found."})

    # Extract relevant information with improved logic
    response_text = get_relevant_info(user_question, case_text)

    return jsonify({"response": response_text})

    return jsonify({"response": response_text})

@app.route('/download_summary/<filename>')
def download_summary(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT summary FROM uploads WHERE username=%s AND filename=%s", (username, filename))
    result = cursor.fetchone()
    db.close()
    
    if result and result[0]:
        summary_content = result[0]
        summary_path = os.path.join(app.config['UPLOAD_FOLDER'], f"summary_{filename}.html")
        with open(summary_path, "w", encoding="utf-8") as file:
            file.write(summary_content)
        return send_file(summary_path, as_attachment=True, mimetype="text/html")
    else:
        return "Summary not found.", 404

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
