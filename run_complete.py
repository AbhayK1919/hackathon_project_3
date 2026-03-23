from flask import Flask, render_template, request, redirect, session, send_from_directory, jsonify
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = "smart-organizer-secret-key-2024"

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "uploads/extracted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

def classify_file(filename):
    name = filename.lower()
    if any(k in name for k in ["dbms", "sql", "database"]): return "DBMS"
    if any(k in name for k in ["os", "process", "thread"]): return "OS"
    if any(k in name for k in ["cn", "network", "tcp"]): return "CN"
    return "Others"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "student" and request.form["password"] == "password123":
            session["user"] = "student"
            return redirect("/dashboard")
    return render_template("login.html", error="Try: student / password123")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/", defaults={"path": ""})
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if "user" not in session:
        return redirect("/login")
    routes = {
        "dashboard": "dashboard.html",
        "files": "files.html", 
        "chat": "chat.html",
        "syllabus": "syllabus.html",
        "notes": "notes.html",
        "calendar": "calendar.html",
        "profile": "profile.html",
        "code": "code.html",
        "doc": "doc.html"
    }
    template = routes.get(path, "dashboard.html")
    stats = {"total_files": 12, "subjects": ["DBMS", "OS", "CN"], "progress": 67, "reminders": 3}
    if path == "files":
        data = {"DBMS": [], "OS": [], "CN": [], "Others": []}
        if os.path.exists(UPLOAD_FOLDER):
            for f in os.listdir(UPLOAD_FOLDER):
                data[classify_file(f)].append(f)
        return render_template(template, data=data, stats=stats, username="Student")
    return render_template(template, stats=stats, username="Student")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if "user" not in session:
        return jsonify({"error": "Login required"}), 401
    data = request.json or {}
    messages = data.get('messages', [])
    user_msg = messages[-1]['content'] if messages else 'Hello'
    
    # Groq LLM if available
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # ChatGPT-like quality
            messages=[
                {"role": "system", "content": "You are a helpful CS study assistant like ChatGPT. Explain concepts clearly for students."},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return jsonify({"reply": response.choices[0].message.content})
    except:
        # Fallback intelligent responses
        lower_msg = user_msg.lower()
        if 'dbms' in lower_msg or 'normalization' in lower_msg:
            reply = """**DBMS Normalization** 📚

Normalization reduces data redundancy:
- **1NF**: Atomic values, no repeating groups
- **2NF**: 1NF + no partial dependency
- **3NF**: 2NF + no transitive dependency
- **BCNF**: Every determinant is candidate key

Example table → Apply step by step? Ask!"""
        elif 'os' in lower_msg or 'scheduler' in lower_msg:
            reply = """**OS Scheduler** ⚙️

CPU Scheduling Algorithms:
1. **FCFS** - First Come First Served (Convoy effect)
2. **SJF** - Shortest Job First (Optimal avg wait time)
3. **Priority** - Priority based (Starvation risk)
4. **RR** - Round Robin (Time quantum)

RR best for time-sharing. Which for realtime systems?"""
        elif 'network' in lower_msg or 'tcp' in lower_msg:
            reply = """**Computer Networks TCP** 🌐

**TCP 3-way Handshake**:
```
Client → SYN → Server
Server → SYN-ACK → Client  
Client → ACK → Server
```

**Congestion Control**: Slow Start → Congestion Avoidance → Fast Recovery

Reliable, connection-oriented. QUIC alternative? Ask!"""
        else:
            reply = """**Study Assistant Ready** 🤖

Ask about:
• DBMS normalization/SQL joins
• OS processes/scheduling/memory
• CN layers/TCP/IP protocols

Or upload syllabus image for analysis! What's your question? 📖"""
        return jsonify({"reply": reply})

@app.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    return jsonify({"subject": "Demo", "content": "Image analyzed! Add OpenAI key."})

if __name__ == '__main__':
    print("🚀 Complete Smart Organizer: http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
