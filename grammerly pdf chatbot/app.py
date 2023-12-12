
import openai
from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import os
import logging

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = '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'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        text = ''
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

def grammar_and_spelling_check(user_text):
    # Check the word count
    word_count = len(user_text.split())
    
    if word_count > 200:
        return "Free Word limit exceeded! Upgrade to Premium Version", 0, 0
    
    prompt = f"Please remove all the grammatical, spelling, and punctuation errors from the following paragraph and return the corrected paragraph with the number of grammatical, spelling, and punctuation errors. give me the number of spelling errors, punctuation errors in separate and new line.\n{user_text}\n"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    assistant_response = response['choices'][0]['message']['content']

    # Count spelling errors
    num_spelling_errors = sum(1 for word in user_text.split() if word != word.capitalize())

    # Count punctuation errors
    num_punctuation_errors = sum(1 for char in user_text if char in ",.?!")

    return assistant_response, num_spelling_errors, num_punctuation_errors

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' in request.files and request.files['file']:
            # User uploaded a file
            pdf_file = request.files['file']
            if pdf_file and allowed_file(pdf_file.filename):
                # Save the uploaded PDF temporarily
                pdf_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
                pdf_file.save(pdf_file_path)

                # Extract text from the PDF
                user_text = extract_text_from_pdf(pdf_file_path)

                # Close the file after extracting text
                pdf_file.close()

                # Delete the temporary PDF file
                os.remove(pdf_file_path)
            else:
                return "Invalid file type. Please upload a PDF file."
        else:
            # User entered text directly
            user_text = request.form.get('user_text', '')

        logging.debug(f"User text: {user_text}")

        corrected_text, num_spelling_errors, num_punctuation_errors = grammar_and_spelling_check(user_text)
        logging.debug(f"Corrected text: {corrected_text}")

        return render_template('index.html',
                               user_text=user_text,
                               corrected_text=corrected_text,
                               num_spelling_errors=num_spelling_errors,
                               num_punctuation_errors=num_punctuation_errors)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    # Create the 'uploads' folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
