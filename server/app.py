from flask import Flask, render_template, request, redirect, url_for, jsonify
import socket
import os
from werkzeug.utils import secure_filename
from trans import process_files
import question_gen
import utils
import json
import slm_analyse

app = Flask(__name__)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use os.path.join for proper path handling
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define file paths
PUBLISHED_TEST_FILE = os.path.join(BASE_DIR, "published_test.json")

# Combined Admin Dashboard
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Handle file uploads
        if 'pdf' in request.files and 'audio' in request.files:
            pdf = request.files['pdf']
            audio = request.files['audio']  
            
            if pdf.filename != '' and audio.filename != '':
                # Save files
                pdf_filename = secure_filename(pdf.filename)
                audio_filename = secure_filename(audio.filename)
                
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
                
                pdf.save(pdf_path)
                audio.save(audio_path)
                
                try:
                    # Process files in parallel
                    updates = []
                    def status_callback(update):
                        updates.append(update)
                    
                    audio_output, pdf_output = process_files(
                        audio_path,
                        pdf_path,
                        status_callback=status_callback
                    )

                    # Read the output files' content
                    audio_text = ""
                    pdf_text = ""
                    try:
                        with open(audio_output, "r", encoding="utf-8") as f:
                            audio_text = f.read()
                    except Exception:
                        audio_text = "Could not read audio transcription output."

                    try:
                        with open(pdf_output, "r", encoding="utf-8") as f:
                            pdf_text = f.read()
                    except Exception:
                        pdf_text = "Could not read PDF extraction output."

                    return jsonify({
                        'success': True,
                        'message': 'Files processed successfully',
                        'updates': updates,
                        'audio_output': audio_output,
                        'pdf_output': pdf_output,
                        'audio_text': audio_text,
                        'pdf_text': pdf_text
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f'Error processing files: {str(e)}'
                    })
        
        # Handle question submission
        question = request.form.get("question")
        if question:
            options = [request.form.get(f"option{i}") for i in range(1, 5)]
            answer = request.form.get("answer")
            utils.save_question(question, options, answer)
            return redirect(url_for("admin"))

    # Load data for display
    questions = utils.load_questions()
    student_data = utils.load_student_analysis()
    return render_template("admin.html", questions=questions, data=student_data)

# Student Test Page
@app.route("/test")
def test():
    questions = []
    if os.path.exists(PUBLISHED_TEST_FILE):
        with open(PUBLISHED_TEST_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)
    return render_template("test.html", questions=questions)

# Submit Test
@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data.get("answers")
    name = data.get("name")
    
    # Get questions from published test
    questions = []
    if os.path.exists(PUBLISHED_TEST_FILE):
        with open(PUBLISHED_TEST_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)
    
    # Save the submission
    utils.save_test_submission(name, questions, answers)
    
    # Calculate and save result
    result = utils.evaluate(answers)
    if name:
        utils.save_student_result(name, result["score"], result["total"])
    return jsonify(result)

@app.route("/generate_questions", methods=["POST"])
def generate_questions():
    try:
        para1, para2 = question_gen.read_paragraphs()
        questions = question_gen.generate_questions(para1, para2)
        return jsonify({"success": True, "questions": questions})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/publish_test", methods=["POST"])
def publish_test():
    try:
        para1, para2 = question_gen.read_paragraphs()
        questions = question_gen.generate_questions(para1, para2)
        with open(PUBLISHED_TEST_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/analyse", methods=["GET"])
def analyse():
    try:
        # Get AI analysis
        analysis_result = slm_analyse.get_analysis()
        
        if not analysis_result["success"]:
            return render_template("analysis.html", error=analysis_result["error"])
        
        # Read the test submissions for display
        submissions = []
        if os.path.exists(utils.TEST_SUBMISSIONS_FILE):
            with open(utils.TEST_SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
                submissions = json.load(f)
        
        # Format the data for display
        analysis_data = {
            "total_submissions": len(submissions),
            "submissions": submissions,
            "ai_analysis": analysis_result["analysis"]
        }
        
        return render_template("analysis.html", data=analysis_data)
    except Exception as e:
        return render_template("analysis.html", error=str(e))

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)