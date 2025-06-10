from flask import Flask, render_template, request, redirect, url_for, jsonify
import socket
import utils

app = Flask(__name__)

# Admin Dashboard
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        question = request.form.get("question")
        options = [request.form.get(f"option{i}") for i in range(1, 5)]
        answer = request.form.get("answer")
        utils.save_question(question, options, answer)
        return redirect(url_for("admin"))
    questions = utils.load_questions()
    return render_template("admin.html", questions=questions)

# Student Test Page
@app.route("/test")
def test():
    questions = utils.load_questions()
    return render_template("test.html", questions=questions)

# Submit Test
@app.route("/submit", methods=["POST"])
def submit():
    answers = request.json.get("answers")
    result = utils.evaluate(answers)
    return jsonify(result)

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)