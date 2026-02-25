from flask import Flask, render_template, request, jsonify, abort, redirect, session
import json
import os
import random

app = Flask(__name__)
app.secret_key = "secret123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTION_BANK_DIR = os.path.join(BASE_DIR, "question_bank")
RESULTS_FILE = os.path.join(BASE_DIR, "results.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# --------------------------------------------------
# INITIALIZE USERS FILE
# --------------------------------------------------
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)


# --------------------------------------------------
# INITIALIZE RESULTS FILE
# --------------------------------------------------
if not os.path.exists(RESULTS_FILE):
    initial_structure = {
        "student_name": "Rahul S",
        "total_attempts": 0,
        "overall_performance": {
            "total_questions": 0,
            "total_correct": 0,
            "total_wrong": 0,
            "overall_accuracy": 0
        },
        "attempt_history": [],
        "stage_summary": {
            f"stage{i}": {
                "attempts": 0,
                "best_score": 0,
                "average_accuracy": 0,
                "weak_topics": [],
                "strong_topics": []
            } for i in range(1, 11)
        }
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_structure, f, indent=2)


# --------------------------------------------------
# LOGIN
# --------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

        user = next((u for u in users if u["username"] == username and u["password"] == password), None)

        if user:
            session["user"] = username
            return redirect("/")

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# --------------------------------------------------
# REGISTER
# --------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

        if any(u["username"] == username for u in users):
            return render_template("register.html", error="Username already exists")

        users.append({"username": username, "password": password})

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)

        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# --------------------------------------------------
# HOME
# --------------------------------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")


# --------------------------------------------------
# MOCK TEST
# --------------------------------------------------
@app.route("/mocktest")
def mocktest():
    if "user" not in session:
        return redirect("/login")

    stages = [
        i for i in range(1, 11)
        if os.path.exists(os.path.join(QUESTION_BANK_DIR, f"stage{i}.json"))
    ]
    return render_template("mocktest.html", stages=stages)


@app.route("/mocktest/stage/<int:stage>")
def mocktest_stage(stage):
    if "user" not in session:
        return redirect("/login")

    json_file = os.path.join(QUESTION_BANK_DIR, f"stage{stage}.json")

    if not os.path.exists(json_file):
        abort(404)

    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in questions:
        if "options" in q:
            random.shuffle(q["options"])

    return render_template(
        "mocktest_stage.html",
        stage=stage,
        questions=json.dumps(questions)
    )


# --------------------------------------------------
# RESULT + PERFORMANCE UPDATE
# --------------------------------------------------
@app.route("/mocktest/<int:stage>/result")
def mocktest_result(stage):
    score = int(request.args.get("score", 0))

    json_file = os.path.join(QUESTION_BANK_DIR, f"stage{stage}.json")

    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total_questions = len(questions)
    correct = score
    wrong = total_questions - correct
    accuracy = round((correct / total_questions) * 100, 2) if total_questions > 0 else 0

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    results["total_attempts"] += 1
    results["overall_performance"]["total_questions"] += total_questions
    results["overall_performance"]["total_correct"] += correct
    results["overall_performance"]["total_wrong"] += wrong

    total_q = results["overall_performance"]["total_questions"]
    total_c = results["overall_performance"]["total_correct"]

    if total_q > 0:
        results["overall_performance"]["overall_accuracy"] = round((total_c / total_q) * 100, 2)

    results["attempt_history"].append({
        "stage": stage,
        "score": score,
        "accuracy": accuracy
    })

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return render_template("mocktest_result.html", stage=stage, score=score)


# --------------------------------------------------
# PERFORMANCE PAGE
# --------------------------------------------------
@app.route("/performance")
def performance_page():
    if "user" not in session:
        return redirect("/login")

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return render_template("performance.html", data=data)


# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)