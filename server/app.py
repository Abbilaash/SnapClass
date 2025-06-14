from flask import Flask, render_template, request, redirect, url_for, jsonify
import socket
import os
from werkzeug.utils import secure_filename
import utils
from pdf_reader import PDFTextImageExtractor
from pdf2image import convert_from_path

app = Flask(__name__)

# Use os.path.join for proper path handling
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Combined Admin Dashboard
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Handle PDF upload
        if 'pdf' in request.files:
            pdf = request.files['pdf']
            if pdf.filename != '':
                filename = secure_filename(pdf.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf.save(pdf_path)
                
                try:
                    extractor = PDFTextImageExtractor()
                    
                    # Get total pages for progress tracking
                    pages = convert_from_path(pdf_path, poppler_path="../venv/Lib/poppler/Library/bin")
                    total_pages = len(pages)
                    
                    # Process the PDF with status updates
                    updates = []
                    def status_callback(message):
                        updates.append(message)
                    
                    pdf_content = extractor.extract_full_content(pdf_path, status_callback=status_callback)
                    report_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_analysis.md')
                    extractor.save_to_markdown(pdf_content, report_path)
                    
                    return jsonify({
                        'success': True,
                        'message': f'PDF processed successfully ({total_pages} pages)',
                        'updates': updates,
                        'report_path': report_path
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f'Error processing PDF: {str(e)}'
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
    questions = utils.load_questions()
    return render_template("test.html", questions=questions)

# Submit Test
@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data.get("answers")
    name = data.get("name")
    result = utils.evaluate(answers)
    if name:
        utils.save_student_result(name, result["score"], result["total"])
    return jsonify(result)

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)