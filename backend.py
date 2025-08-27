from flask import Flask, request, jsonify
import json
import os
import smtplib, ssl
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ----------------------------
# Setup paths
# ----------------------------
DATA_FOLDER = "data"
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")
INBOX_FILE = os.path.join(DATA_FOLDER, "inbox.json")
os.makedirs(DATA_FOLDER, exist_ok=True)

# Initialize JSON files if they don't exist
for f, default in [(USERS_FILE, {}), (INBOX_FILE, {})]:
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump(default, fp)

# ----------------------------
# Helper functions
# ----------------------------
def load_json(path):
    with open(path, "r") as fp:
        return json.load(fp)

def save_json(path, data):
    with open(path, "w") as fp:
        json.dump(data, fp, indent=2)

# ----------------------------
# SMTP send email (any provider)
# ----------------------------
def send_email_smtp(from_email, password, to_email, subject, body, smtp_server, port=465, use_ssl=True):
    message = f"From: {from_email}\nTo: {to_email}\nSubject: {subject}\n\n{body}"

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(from_email, password)
                server.sendmail(from_email, to_email, message)
        else:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls(context=ssl.create_default_context())
            server.login(from_email, password)
            server.sendmail(from_email, to_email, message)
            server.quit()
        print(f"Email sent to {to_email} via {smtp_server}")
        return True, "Email sent"
    except Exception as e:
        print("Error sending email:", e)
        return False, str(e)

# ----------------------------
# Routes
# ----------------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Missing email or password"}), 400

    users = load_json(USERS_FILE)
    if email in users:
        return jsonify({"success": False, "message": "Email already exists"}), 400

    users[email] = {"password": generate_password_hash(password)}
    save_json(USERS_FILE, users)
    return jsonify({"success": True, "message": "Signup successful"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    users = load_json(USERS_FILE)
    if email not in users or not check_password_hash(users[email]["password"], password):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    return jsonify({"success": True, "message": "Login successful"}), 200

@app.route("/send", methods=["POST"])
def send_email():
    data = request.json
    required_fields = ["from_email", "password", "to_email", "subject", "body", "smtp_server"]
    if any(field not in data for field in required_fields):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    ok, msg = send_email_smtp(
        from_email=data["from_email"],
        password=data["password"],
        to_email=data["to_email"],
        subject=data["subject"],
        body=data["body"],
        smtp_server=data["smtp_server"],
        port=data.get("port", 465),
        use_ssl=data.get("use_ssl", True)
    )

    # Save sent email locally
    inbox = load_json(INBOX_FILE)
    inbox.setdefault(data["from_email"], []).append({
        "to": data["to_email"],
        "subject": data["subject"],
        "body": data["body"]
    })
    save_json(INBOX_FILE, inbox)

    return jsonify({"success": ok, "message": msg})

@app.route("/inbox/<email>", methods=["GET"])
def inbox(email):
    inbox = load_json(INBOX_FILE)
    return jsonify(inbox.get(email, []))

@app.route("/delete", methods=["POST"])
def delete_email():
    data = request.json
    user_email = data.get("email")
    index = data.get("index")
    inbox = load_json(INBOX_FILE)

    if user_email not in inbox or index is None or index >= len(inbox[user_email]):
        return jsonify({"success": False, "message": "Email not found"}), 404

    inbox[user_email].pop(index)
    save_json(INBOX_FILE, inbox)
    return jsonify({"success": True, "message": "Email deleted"})

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
