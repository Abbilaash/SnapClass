import json
import os
import datetime

# Get the directory where utils.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define file paths using absolute paths
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
STUDENT_DATA_FILE = os.path.join(BASE_DIR, "student_analysis.json")
TEST_SUBMISSIONS_FILE = os.path.join(BASE_DIR, "test_submissions.json")


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


def save_test_submission(name, questions, answers):
    """Save a student's test submission to a JSON file"""
    submissions = []
    if os.path.exists(TEST_SUBMISSIONS_FILE):
        with open(TEST_SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
            try:
                submissions = json.load(f)
            except:
                submissions = []
    
    # Create submission object
    submission = {
        "student_name": name,
        "timestamp": str(datetime.datetime.now()),
        "questions_and_answers": [
            {"question": q, "answer": a} 
            for q, a in zip(questions, answers)
        ]
    }
    
    submissions.append(submission)
    
    with open(TEST_SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2)