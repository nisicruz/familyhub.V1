import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///familyhub.V1.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/budget")
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not email or not password or not confirmation:
            flash("All fields required.")
            return render_template("register.html")
        if password != confirmation:
            flash("Passwords do not match.")
            return render_template("register.html")
        hash_pw = generate_password_hash(password)
        try:
            user_id = db.execute("INSERT INTO users (email, hash) VALUES (?, ?)", email, hash_pw)
        except Exception:
            flash("Email already registered.")
            return render_template("register.html")
        session["user_id"] = user_id
        return redirect("/budget")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Email and password required.")
            return render_template("login.html")
        user = db.execute("SELECT * FROM users WHERE email = ?", email)
        if not user or not check_password_hash(user[0]["hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")
        session["user_id"] = user[0]["id"]
        return redirect("/budget")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/budget", methods=["GET", "POST"])
def budget():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    if request.method == "POST":
        date = request.form.get("date")
        type_ = request.form.get("type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        note = request.form.get("note")
        if not date or not type_ or not category or not amount:
            flash("Please complete all fields.")
        else:
            try:
                amount = float(amount)
            except ValueError:
                flash("Amount must be a number.")
                return redirect("/budget")
            db.execute("INSERT INTO transactions (user_id, date, type, category, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
                       user_id, date, type_, category, amount, note)
            flash("Transaction added!")
        return redirect("/budget")

    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND deleted = 0 ORDER BY date DESC",
        user_id
    )
    income = db.execute(
        "SELECT IFNULL(SUM(amount),0) as total FROM transactions WHERE user_id = ? AND type = 'income' AND deleted = 0",
        user_id
    )[0]['total']
    expense = db.execute(
        "SELECT IFNULL(SUM(amount),0) as total FROM transactions WHERE user_id = ? AND type = 'expense' AND deleted = 0",
        user_id
    )[0]['total']
    balance = income - expense

    return render_template("budget.html", transactions=transactions, income=income, expense=expense, balance=balance)

@app.route("/delete/<int:tid>", methods=["POST"])
def delete_transaction(tid):
    if "user_id" not in session:
        return redirect("/login")
    db.execute("UPDATE transactions SET deleted = 1 WHERE id = ?", tid)
    session["undo_tid"] = tid
    flash("Transaction deleted! <a href='/undo_delete' class='alert-link'>Undo</a>", "danger")
    return redirect("/budget")

@app.route("/undo_delete")
def undo_delete():
    if "user_id" not in session or "undo_tid" not in session:
        return redirect("/login")
    tid = session.pop("undo_tid", None)
    if tid:
        db.execute("UPDATE transactions SET deleted = 0 WHERE id = ?", tid)
        flash("Transaction restored.", "success")
    return redirect("/budget")

# Add your export, edit, and other routes as needed!

if __name__ == "__main__":
    app.run(debug=True)
