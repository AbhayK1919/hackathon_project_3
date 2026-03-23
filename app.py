from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
from PIL import Image
import base64
import io

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', "smart-organizer-secret-key-2024")

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "uploads/extracted"
TEMPLATES_FOLDER = "templates"
STATIC_FOLDER = "static"

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, EXTRACTED_FOLDER, TEMPLATES_FOLDER, STATIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Clients
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def classify_file(filename):
    """AI-powered file classification using vision if image"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "Others"
    
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        try:
            # Use OpenAI vision for classification
            subject = analyze_image_content(filepath)
            return subject
        except:
            pass  # Fallback to keywords
    
    # Keyword fallback
    name = filename.lower()
    if any(keyword in name for keyword in ["dbms", "sql", "database", "join", "normalization"]):
        return "DBMS"
    elif any(keyword in name for keyword in ["os", "process", "thread", "memory", "scheduler"]):
        return "OS"
    elif any(keyword in name for keyword in ["cn", "network", "tcp", "udp", "http"]):
        return "CN"
    else:
        return "Others"

def analyze_image_content(image_path):
    """Analyze image with OpenAI GPT-4o-mini-vision for subject/content extraction"""
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this academic image/syllabus. Classify into DBMS, OS, CN, or Others. Respond ONLY with the subject name (e.g., 'DBMS')."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        max_tokens=10
    )
    subject = response.choices[0].message.content.strip().upper()
    if subject in ['DBMS', 'OS', 'CN']:
        return subject
    return 'Others'

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({"error": "No messages"}), 400
    
    try:
        chat_history = [
            {"role": "system", "content": "You are an expert study assistant for Computer Science students. Explain DBMS, OS, CN concepts clearly with examples. Be concise, use bullet points, suggest practice questions."}
        ] + messages
        
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # Fast free model
            messages=chat_history,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_reply = response.choices[0].message.content
        return jsonify({"reply": ai_reply})
    
    except Exception as e:
        return jsonify({"reply": f"Sorry, AI service temporarily unavailable. Error: {str(e)}. Try keyword questions in chat."})

@app.route("/api/analyze-image", methods=["POST"])
def api_analyze_image():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save temp
    temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(temp_path)
    
    try:
        subject = classify_file(file.filename)
        content = analyze_image_content(temp_path)
        
        # Save extracted content
        extracted_path = os.path.join(EXTRACTED_FOLDER, f"{file.filename}.txt")
        with open(extracted_path, 'w') as f:
            f.write(content)
        
        return jsonify({
            "subject": subject,
            "content": content[:500] + "..." if len(content) > 500 else content,
            "extracted_file": f"{file.filename}.txt"
        })
    except Exception as e:
        return jsonify({"error": str(e), "subject": "Others"})

# Existing routes unchanged...
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "student" and password == "password123":
            session["user"] = username
            return redirect("/")
        else:
            error = "Invalid username or password. Try: student / password123"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    # Dashboard stats (mock data for demo) - TODO: make real
    stats = {
        "total_files": 12,
        "subjects": ["DBMS", "OS", "CN"],
        "progress": 67,
        "reminders": 3
    }
    
    return render_template("dashboard.html", stats=stats, username=session.get("user", "Student"))

@app.route("/files", methods=["GET", "POST"])
def files():
    if "user" not in session:
        return redirect("/login")
    
    preview_file = None
    preview_analysis = None
    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)
                preview_file = file.filename
                # Auto-analyze image
                preview_analysis = analyze_image_content(filepath)
    
    # Get classified files
    data = {"DBMS": [], "OS": [], "CN": [], "Others": []}
    
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            subject = classify_file(filename)
            data[subject].append(filename)
    
    return render_template("files.html", data=data, username=session.get("user", "Student"), preview_file=preview_file, preview_analysis=preview_analysis)

@app.route("/search")
def search():
    if "user" not in session:
        return redirect("/login")
    
    query = request.args.get("q", "").lower().strip()
    search_data = {"DBMS": [], "OS": [], "CN": [], "Others": []}
    
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if query and query not in filename.lower():
                continue
            subject = classify_file(filename)
            search_data[subject].append(filename)
    
    return render_template("files.html", data=search_data, username=session.get("user", "Student"), query=query, preview_file=None)

@app.route("/doc/<filename>")
def doc(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    subject = classify_file(filename)
    subject_keywords = {
        "DBMS": "Database Management Systems Notes Syllabus",
        "OS": "Operating Systems Processes Threads Notes",
        "CN": "Computer Networks TCP UDP Syllabus",
        "Others": "Study Materials Notes"
    }.get(subject, "Study Document")
    
    return render_template("doc.html", filename=filename, subject=subject, desc=subject_keywords)

@app.route("/syllabus")
def syllabus():
    if "user" not in session:
        return redirect("/login")
    return render_template("syllabus.html", username=session.get("user", "Student"))

@app.route("/notes")
def notes():
    if "user" not in session:
        return redirect("/login")
    return render_template("notes.html", username=session.get("user", "Student"))

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", username=session.get("user", "Student"))

@app.route("/calendar")
def calendar():
    if "user" not in session:
        return redirect("/login")
    return render_template("calendar.html", username=session.get("user", "Student"))

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    return render_template("profile.html", username=session.get("user", "Student"))

@app.route("/code")
def code():
    if "user" not in session:
        return redirect("/login")
    return render_template("code.html", username=session.get("user", "Student"))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if "user" not in session:
        return redirect("/login")
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/extracted/<filename>')
def extracted_file(filename):
    if "user" not in session:
        return redirect("/login")
    return send_from_directory(EXTRACTED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
