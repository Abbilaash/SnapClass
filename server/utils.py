import json
import os

QUESTIONS_FILE = "questions.json"
STUDENT_DATA_FILE = "student_analysis.json"


def save_question(question, options, answer):
    data = load_questions()
    data.append({
        "question": question,
        "options": options,
        "answer": answer
    })
    with open(QUESTIONS_FILE, "w") as f:
        json.dump(data, f)


def load_questions():
    try:
        with open(QUESTIONS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def evaluate(student_answers):
    correct = 0
    total = len(student_answers)
    data = load_questions()
    for i, user_answer in enumerate(student_answers):
        if i < len(data) and data[i]["answer"] == user_answer:
            correct += 1
    return {"score": correct, "total": total}


def save_student_result(name, score, total):
    data = []
    if os.path.exists(STUDENT_DATA_FILE):
        with open(STUDENT_DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = []
    data.append({"name": name, "score": score, "total": total})
    with open(STUDENT_DATA_FILE, "w") as f:
        json.dump(data, f)


def load_student_analysis():
    if os.path.exists(STUDENT_DATA_FILE):
        with open(STUDENT_DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []