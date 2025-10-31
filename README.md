# 🧾 Chickle Contract Analyzer

**Chickle Contract Analyzer** is an AI-powered backend built using **Flask** and **Google Gemini 2.5 Pro**.  
It intelligently analyzes, summarizes, and interprets **legal contracts or uploaded PDF documents**, returning structured Markdown-based responses for seamless frontend display.

🔗 **Live Website:** [Chickle Contract Analyzer](https://chicklelegalcontractanalyzer.netlify.app/)

---

## ⚙️ Features

- 🧠 **AI-Driven Legal Analysis** (Gemini 2.5 Pro)
- 📄 **PDF Document Parsing** using `pdfplumber`
- 🧹 **Clean Markdown Output** optimized for frontend rendering
- 🌐 **CORS Enabled** Flask API for web integration
- ⚖️ **Smart Query Classification** (detects contract vs. general legal query)
- 💬 **Predefined Legal Responses** for greetings, errors, or unrelated inputs
- 🪶 **Lightweight Flask Backend**, deployable on any Python environment

---

## 🧩 Project Structure

📦 Chickle Contract Analyzer
│
├── app.py # Flask backend
├── requirements.txt # Python dependencies
├── README.md # Documentation
└── static/ / templates/ 


---

## 🧠 Core Logic Overview

### 1. Gemini AI Setup
``python
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-2.5-pro")
Configures Gemini 2.5 Pro for generating legal insights and contract interpretations.

2. Markdown Cleaning
Removes HTML tags, extra spaces, and ensures clean, structured Markdown formatting for the frontend.

3. Query Handling
Handles both:

Text-based legal queries

PDF-based contract uploads

If a PDF is uploaded, text is extracted with pdfplumber before sending to Gemini for interpretation.

4. Smart Prompt Engineering
Gemini is instructed to:

Use ## for headings, ### for subheadings

Use bullet points (-) for clarity

Highlight legal terms in bold

Remain professional, concise, and structured

Redirect contract-related queries to the Contract Analyzer site

5. PDF Extraction
python
Copy code
with pdfplumber.open(BytesIO(file.read())) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
Extracts readable text from uploaded legal documents for accurate analysis.

🧰 API Endpoint
POST /ask
Content Types:
application/json

multipart/form-data (for PDF upload)

JSON Example:
json
Copy code
{
  "query": "Explain the confidentiality clause in this contract."
}
Form-Data Example:
Key	Type	Description
query	text	Legal question
file	file (.pdf)	Optional uploaded contract document

Sample Response:
json
Copy code
{
  "response": "## Confidentiality Clause\n- **Party A** must not disclose any proprietary information...\n- **Party B** shall maintain confidentiality for 2 years post-agreement."
}
⚠️ Predefined Responses
Query Type	AI Response
Greeting (hi/hello)	“Hello! I’m Chickle, your AI Legal Assistant. How can I assist you today?”
Contract-related (draft/review/modify)	“⚠️ I focus only on general legal assistance.\n\nPlease use Chickle’s Contract Analyzer instead:\n👉 Chickle - Contract Analyzer”
Non-legal question	“⚠️ This is not a legal question. I can only answer legal queries.”
Capabilities/Help query	Lists supported legal domains (Civil, Corporate, IP, Family, etc.)

🧑‍💻 Installation & Setup
Prerequisites
Python 3.9+

Google Generative AI API key

Flask, Flask-CORS, and pdfplumber installed

Setup Steps
bash
Copy code
# Clone this repository
git clone https://github.com/<your-repo>/chickle-contract-analyzer.git
cd chickle-contract-analyzer

# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
Server starts at:

cpp
Copy code
http://127.0.0.1:5000
🧩 Dependencies
nginx
Copy code
Flask
Flask-Cors
google-generativeai
pdfplumber
🌐 Deployment
Compatible with:

Render

Railway

PythonAnywhere

GCP / AWS / Azure

Before deployment, export your API key:

bash
Copy code
export GOOGLE_API_KEY="your_api_key"
🔒 Notes
Keep your API key private.

Only supports text-based PDFs (not scanned images).

Markdown output is optimized for frontend display.

🧾 Example Use Case
User Query:

“Analyze the termination and indemnity clauses in this document.”

AI Response:

markdown
Copy code
## Termination & Indemnity Clauses
- **Party A** may terminate with 30 days' notice.  
- **Party B** must indemnify for losses caused by contract breach.  
- **Liability Cap:** Limited to direct damages only.
🌐 Live Project
🚀 Frontend: https://chicklelegalcontractanalyzer.netlify.app/
💬 Purpose: Upload contracts or ask clause-specific questions for instant legal insights.

🧑‍⚖️ Author
Mohamed Asif (Asi)
B.Sc Artificial Intelligence & Machine Learning
Final Year Project — AI Legal Contract Analyzer and Creator
📁 Portfolio: https://mdasif-portfolio.netlify.app


