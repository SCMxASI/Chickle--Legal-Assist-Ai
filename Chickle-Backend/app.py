from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS
import pdfplumber
from io import BytesIO
import re

app = Flask(__name__)
CORS(app)

# Gemini API setup
genai.configure(api_key="AIzaSyDRt69Gh0RrPFfSVgiQ4yOy-MwIYuKhfnI")
model = genai.GenerativeModel("gemini-2.5-pro")

def clean_markdown(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{3,}([^*]+)\*{3,}', r'**\1**', text)  # fix ***bold*** misuse
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    cleaned = '\n'.join(line for line in lines if line)
    return cleaned.strip()

def query_gemini_for_legal(query, is_file=False):
    try:
        if is_file:
            final_prompt = query
        else:
            final_prompt = f"""
You are Chickle, an AI Legal Expert. Provide clear, structured legal responses based on the user query.

### Guidelines:
- Use ## for main sections and ### for subsections
- Use bullet points (-) for lists
- Use **bold** for legal terms and key phrases
- Be concise, professional, and avoid unnecessary formatting
- If the user greets (e.g., "hi", "hello"), reply:
"Hello! I’m Chickle, your AI Legal Assistant. How can I assist you today?"
- If the query is **contract-related** (e.g., drafting, reviewing, analyzing, modifying, interpreting), do NOT answer. Instead, reply:
"⚠️ I focus only on general legal assistance.\n\nPlease use Chickle’s Contract Analyzer instead:\n👉 [Chickle - Contract Analyzer](https://chicklelegalcontractanalyzer.netlify.app/)"

## My Capabilities

I can assist with legal case files and queries related to:

- ⚖️ General Law  
- 🧑‍💼 Employment Law  
- 🏢 Corporate Law  
- 🧠 Intellectual Property  
- 🏠 Property Law  
- 👨‍👩‍👧‍👦 Family Law  
- 🌐 Data / IT / Privacy  
- 📑 Regulatory / Compliance  
- 🏛️ Litigation & Dispute Resolution  
- 🟤 Civil & Criminal Law  

I can also answer general legal questions across all jurisdictions.

Only respond to legal questions. If the query is unrelated to law, say:
"⚠️ This is not a legal question. I can only answer legal queries."

User query: {query}
"""
        response = model.generate_content(final_prompt)
        return clean_markdown(response.text)
    except Exception as e:
        print(f"[ERROR] Gemini query failed: {e}")
        return "⚠️ Failed to process query. Please try again later."

@app.route("/ask", methods=["POST"])
def ask_legal_ai():
    user_query = ""
    pdf_text = ""

    try:
        if request.content_type.startswith("multipart/form-data"):
            user_query = request.form.get("query", "").strip()
            file = request.files.get("file")
            if file and file.filename.lower().endswith(".pdf"):
                try:
                    with pdfplumber.open(BytesIO(file.read())) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                pdf_text += text + "\n"
                    pdf_text = pdf_text.strip()
                    if not pdf_text:
                        return jsonify({"response": "⚠️ The uploaded PDF appears to be empty or unreadable."})
                except Exception as e:
                    print(f"[ERROR] PDF extraction failed: {e}")
                    return jsonify({"response": "⚠️ Failed to read PDF."})
        else:
            data = request.json
            user_query = data.get("query", "").strip()

        lower_query = user_query.lower()
        print("[INFO] /ask was called. Query:", user_query)

        if not user_query:
            return jsonify({"error": "No query provided"}), 400

        # Reserved hardcoded queries
        if any(phrase in lower_query for phrase in ["who are you", "what is your name", "who r u"]):
            response_text = "I am Chickle, your AI Legal Assistant."

        elif any(phrase in lower_query for phrase in [
            "what you can do", "what can you do", "how can you help", "your use",
            "your features", "how do you assist", "your work", "your capabilities",
            "your functions", "what are you", "help me with", "what services",
            "what's your use", "what do you do"
        ]):
            response_text = """## My Capabilities

I can assist with legal case files and queries related to:

- ⚖️ General Law  
- 🧑‍💼 Employment Law  
- 🏢 Corporate Law  
- 🧠 Intellectual Property  
- 🏠 Property Law  
- 👨‍👩‍👧‍👦 Family Law  
- 🌐 Data/IT/Privacy  
- 📑 Regulatory/Compliance  
- 🏛️ Litigation & Dispute Resolution  
- 🟤 Civil & Criminal Law  

Additionally, I can answer general legal queries across all jurisdictions."""

        else:
            if pdf_text:
                combined_prompt = f"""
The user uploaded a legal document and asked the following question. Read and answer strictly based on document content.

--- Document Content ---
{pdf_text}

--- User Query ---
{user_query}
"""
                response_text = query_gemini_for_legal(combined_prompt, is_file=True)
            else:
                response_text = query_gemini_for_legal(user_query)

    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        response_text = "⚠️ Internal error. Please try again later."

    return jsonify({"response": clean_markdown(response_text).strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
