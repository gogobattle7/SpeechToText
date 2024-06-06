import os
from flask import Flask, request, render_template, send_file
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file.save('uploaded_audio.m4a')
        subprocess.run(['python', 'speechToText.py'])  # Run the speech-to-text script
        return 'success'

@app.route('/refine', methods=['POST'])
def refine_file():
    if 'formFile' not in request.files:
        return 'No form file part'
    form_file = request.files['formFile']
    if form_file.filename == '':
        return 'No selected form file'
    if form_file:
        form_file.save('form.pdf')
        # Run the transcript.py script
        subprocess.run(['python', 'transcript.py'])
        return send_file('refined_transcript.pdf', as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)