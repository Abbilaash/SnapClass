import json

QUESTIONS_FILE = "questions.json"

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