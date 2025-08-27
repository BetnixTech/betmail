from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, smtplib, ssl, os

app = Flask(__name__)
DB_FILE = "webmail.db"

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE emails
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, recipient TEXT, subject TEXT, body TEXT, draft INTEGER DEFAULT 0, trash INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

init_db()

@app.route("/")
def index():
    return send_from_directory("", "index.html")

@app.route("/<path:path>")
def serve_file(path):
    return send_from_directory("", path)

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    hashed = generate_password_hash(data["password"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (data["name"], data["email"], hashed))
        conn.commit()
        return jsonify({"status":"ok"})
    except sqlite3.IntegrityError:
        return jsonify({"status":"error","message":"Email already registered"}), 400
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password, name FROM users WHERE email=?", (data["email"],))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], data["password"]):
        return jsonify({"status":"ok", "name": row[1]})
    else:
        return jsonify({"status":"error","message":"Invalid login"}), 400

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "YOUR_EMAIL@gmail.com"
SMTP_PASS = "YOUR_PASSWORD"

def send_smtp(to_addr, subject, body):
    message = f"Subject: {subject}\n\n{body}"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_addr, message)

@app.route("/send", methods=["POST"])
def send_email():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO emails (sender,recipient,subject,body,draft) VALUES (?,?,?,?,?)",
              (data["from"], data["to"], data["subject"], data["body"], 1 if data.get("draft") else 0))
    conn.commit()
    conn.close()
    if not data.get("draft"):
        try:
            send_smtp(data["to"], data["subject"], data["body"])
        except Exception as e:
            print("SMTP error:", e)
    return jsonify({"status":"ok"})

@app.route("/emails/<email>")
def get_emails(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,sender,recipient,subject,body,draft,trash,timestamp FROM emails WHERE sender=? OR recipient=? ORDER BY timestamp DESC", (email,email))
    rows = c.fetchall()
    conn.close()
    emails = [{"id":r[0],"from":r[1],"to":r[2],"subject":r[3],"body":r[4],"draft":r[5],"trash":r[6],"timestamp":r[7]} for r in rows]
    return jsonify(emails)

@app.route("/delete", methods=["POST"])
def delete_email():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE emails SET trash=1 WHERE id=?", (data["id"],))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
