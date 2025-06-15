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

def generate_questions(para1, para2, num_questions=5):
    # Dummy question generation for demonstration
    questions = []
    payload = {
        "message": f"""Based on the paragraphs {para1} and {para2}, generate {num_questions} descriptive questions that test 
        understanding of the key concepts.
        The questions you are taking should be common to both the paragraphs.""",
        "mode": "chat",  # or "query"
        "sessionId": "my-session-id",
        "attachments": [],
        "reset": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # ✅ Send the request
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())
    questions = response.json().get('textResponse', 'No response key found').split('\n\n')[:-1]
    return questions