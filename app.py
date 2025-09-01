from flask import Flask, render_template, request, redirect
from intasend import APIService
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Debug: print to confirm keys are being loaded
print("SECRET:", os.getenv("INTASEND_SECRET_KEY"))
print("PUB:", os.getenv("INTASEND_PUBLISHABLE_KEY"))

app = Flask(__name__)

# IntaSend setup
publishable_key = os.getenv("INTASEND_PUBLISHABLE_KEY")
secret_key = os.getenv("INTASEND_SECRET_KEY")

service = APIService(
    token=secret_key,
    publishable_key=publishable_key,
    test=True  # switch to False when going live
)

# Database helper
def get_db():
    conn = sqlite3.connect("journal.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM journal_entries ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", entries=entries)

@app.route("/add", methods=["POST"])
def add_entry():
    title = request.form["title"]
    content = request.form["content"]
    conn = get_db()
    conn.execute(
        "INSERT INTO journal_entries (title, content) VALUES (?, ?)", 
        (title, content)
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/donate", methods=["POST"])
def donate():
    phone = request.form["phone"]
    email = request.form["email"]
    amount = float(request.form["amount"])

    # Save donation locally
    conn = get_db()
    conn.execute(
        "INSERT INTO donations (phone, email, amount) VALUES (?, ?, ?)", 
        (phone, email, amount)
    )
    conn.commit()
    conn.close()

    # Create IntaSend checkout session
    response = service.collect.checkout(
        phone_number=phone,
        email=email,
        amount=amount,
        currency="KES",
        comment="Journal Support Donation",
        redirect_url="http://127.0.0.1:5000/thank-you"
    )

    # Redirect donor to IntaSend payment page
    return redirect(response.get("url"))

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")

@app.route("/dashboard")
def dashboard():
    conn = get_db()
    donations = conn.execute(
        "SELECT amount, created_at FROM donations"
    ).fetchall()
    conn.close()

    labels = [row["created_at"] for row in donations]
    amounts = [row["amount"] for row in donations]

    return render_template("dashboard.html", labels=labels, amounts=amounts)

if __name__ == "__main__":
    # Ensure DB exists with required tables
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS donations (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, email TEXT, amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.close()
    app.run(debug=True)
