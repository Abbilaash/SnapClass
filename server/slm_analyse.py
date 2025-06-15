# model used: phi3.5

import requests
import yaml
import os
import json

# ✅ Load config from config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

API_KEY = config["api_key"]
BASE_URL = config["model_server_base_url"]
WORKSPACE_SLUG = config["workspace_slug"]

# ✅ Construct the endpoint
url = f"{BASE_URL}/workspace/{WORKSPACE_SLUG}/chat"

def read_paragraphs():
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    para1_path = os.path.join(base_dir, "class_audio_transcription.md")
    para2_path = os.path.join(base_dir, "sample_content.md")
    with open(para1_path, "r", encoding="utf-8") as f:
        para1 = f.read()
    with open(para2_path, "r", encoding="utf-8") as f:
        para2 = f.read()
    return para1, para2


def read_submissions():
    """Read and organize questions and answers from test_submissions.json"""
    try:
        submissions_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_submissions.json")
        with open(submissions_file, "r", encoding="utf-8") as f:
            submissions = json.load(f)
        
        # Get unique questions from the first submission
        questions = []
        if submissions:
            questions = [qa["question"] for qa in submissions[0]["questions_and_answers"]]
        
        # Organize answers by student
        student_answers = {}
        for submission in submissions:
            student_name = submission["student_name"]
            answers = [qa["answer"] for qa in submission["questions_and_answers"]]
            student_answers[student_name] = answers
        
        return {
            "questions": questions,
            "student_answers": student_answers
        }
    except FileNotFoundError:
        print("test_submissions.json not found")
        return {"questions": [], "student_answers": {}}
    except Exception as e:
        print(f"Error reading submissions: {str(e)}")
        return {"questions": [], "student_answers": {}}


def get_analysis():
    """Get analysis of student submissions using the AI model"""
    try:
        # Get submissions and paragraphs
        submissions_data = read_submissions()
        para1, para2 = read_paragraphs()
        
        # Prepare the message for the AI model
        payload = {
            "message": f"""Analyze the following test submissions and provide insights:

Materials used for questions:
1. Audio Transcription: {para1}
2. Sample Content: {para2}

Questions asked: {submissions_data['questions']}

Student Answers: {submissions_data['student_answers']}

Please provide:
1. Overall class performance analysis
2. Common misconceptions or areas where students struggled
3. Suggestions for improvement
4. Individual student performance highlights""",
            "mode": "chat",
            "sessionId": "analysis-session",
            "attachments": [],
            "reset": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        response = requests.post(url, headers=headers, json=payload)
        analysis_text = response.json().get('textResponse', 'No analysis available')
        
        return {
            "success": True,
            "analysis": analysis_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
