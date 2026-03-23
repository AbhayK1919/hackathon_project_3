from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import os
try:
    from dotenv import load_dotenv
except ImportError:
    print("dotenv not installed, using os.getenv with placeholders")
    load_dotenv = lambda: None

try:
    from openai import OpenAI
    from groq import Groq
    AI_AVAILABLE = True
except ImportError:
    print("AI libs not fully installed, using dummy responses")
    AI_AVAILABLE = False

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', "smart-organizer-secret-key-2024")

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "uploads/extracted"
TEMPLATES_FOLDER = "templates"
STATIC_FOLDER = "static"

for folder in [UPLOAD_FOLDER, EXTRACTED_FOLDER, TEMPLATES_FOLDER, STATIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def dummy_chat_reply(messages):
    return "AI demo: Great question on studies! (Add real Groq/OpenAI keys to .env for full LLM)"

def dummy_analyze_image(image_path):
    return "Demo: Syllabus looks like DBMS. (Add OpenAI key)"

if AI_AVAILABLE:
    groq_client = Groq(api_key=os.getenv('GROQ_API_KEY', ''))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', ''))
    
    def classify_file(filename):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')) and os.path.exists(filepath):
            try:
                import base64
                with open(filepath, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Classify this academic image into DBMS, OS, CN, Others. Respond ONLY subject."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=10
                )
                subject = response.choices[0].message.content.strip().upper()
                if subject in ['DBMS', 'OS', 'CN']:
                    return subject
            except:
                pass
        # Keyword fallback
        name = filename.lower()
        if 'dbms' in name or 'sql' in name:
            return "DBMS"
        elif 'os' in name or 'process' in name:
            return "OS"
        elif 'cn' in name or 'network' in name:
            return "CN"
        return "Others"
else:
    def classify_file(filename):
        # Keyword only
        name = filename.lower()
        if 'dbms' in name or 'sql' in name:
            return "DBMS"
        elif 'os' in name or 'process' in name:
            return "OS"
        elif 'cn' in name or 'network' in name:
            return "CN"
        return "Others"

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"reply": "Send a message!"})
    try:
        if AI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            chat_history = [{"role": "system", "content": "CS study assistant expert."}] + messages
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=chat_history,
                max_tokens=500
            )
            return jsonify({"reply": response.choices[0].message.content})
        else:
            return jsonify({"reply": dummy_chat_reply(messages)})
    except Exception as e:
        return jsonify({"reply": f"Demo mode: {str(e)}. Add API keys."})

@app.route("/api/analyze-image", methods=["POST"])
def api_analyze_image():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file"})
    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    try:
        subject = classify_file(file.filename)
        content = dummy_analyze_image(filepath) if not AI_AVAILABLE else "AI analyzed"  # Simplified no PIL
        return jsonify({"subject": subject, "content": content})
    except:
        return jsonify({"subject": classify_file(file.filename), "content": "Demo analysis"})

# All other routes unchanged...
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "student" and request.form.get("password") == "password123":
            session["user"] = "student"
            return redirect("/")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/")
def home():
    return redirect("/dashboard") if "user" in session else redirect("/login")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", stats={"total_files": len(os.listdir(UPLOAD_FOLDER) if os.path.exists(UPLOAD_FOLDER) else 0), "progress": 67}, username="Student")

@app.route("/files", methods=["GET", "POST"])
def files():
    if "user" not in session:
        return redirect("/login")
    data = {"DBMS": [], "OS": [], "CN": [], "Others": []}
    if os.path.exists(UPLOAD_FOLDER):
        for f in os.listdir(UPLOAD_FOLDER):
            s = classify_file(f)
            data[s].append(f)
    return render_template("files.html", data=data, username="Student")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", username="Student")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    print("🚀 Smart Organizer running on http://0.0.0.0:5000 (AI demo mode - add keys for full!)")
    app.run(debug=True, host="0.0.0.0", port=5000)
