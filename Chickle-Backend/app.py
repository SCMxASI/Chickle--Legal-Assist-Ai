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
    """
    Simple markdown cleaning that fixes structure without causing weird line gaps.
    """
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Fix excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Fix markdown formatting issues
    text = re.sub(r'\*{3,}([^*]+)\*{3,}', r'**\1**', text)  # Fix excessive asterisks

    # Clean up the final result
    text = text.strip()

    return text

def query_gemini_for_legal(query, is_file=False):
    """Generate a legal answer using Gemini."""
    try:
        if is_file:
            final_prompt = query
        else:
            final_prompt = f"""
You are Chickle, an AI Legal Expert. Provide clear, well-structured responses.

Important guidelines:
- Use ## for main sections and ### for subsections
- Use bullet points (-) for lists
- Use **bold** for important legal terms
- Keep paragraphs concise and well-separated
- Avoid excessive line breaks or formatting

Only answer legal questions. If not legal-related, respond:
"⚠️ This is not a legal question. I can only answer legal queries."

User query: {query}
"""

        # Generate the response
        response = model.generate_content(final_prompt)
        raw_output = response.text
        return clean_markdown(raw_output)

    except Exception as e:
        print(f"[ERROR] Gemini query failed: {e}")
        return "⚠️ Failed to process query. Please try again later."

@app.route("/ask", methods=["POST"])
def ask_legal_ai():
    """Handle /ask endpoint with clean, properly formatted output."""
    user_query = ""
    pdf_text = ""

    try:
        if request.content_type.startswith("multipart/form-data"):
            user_query = request.form.get("query", "").strip()
            file = request.files.get("file")
            if file and file.filename != "":
                try:
                    with pdfplumber.open(BytesIO(file.read())) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                pdf_text += text + "\n"
                    pdf_text = pdf_text.strip()
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

        # Handle special/reserved queries with clean formatting
        if "who are you" in lower_query or "what is your name" in lower_query or "who r u" in lower_query:
            response_text = "I am Chickle, your AI Legal Assistant."

        elif any(phrase in lower_query for phrase in [
            "analyze contract", "analyze this contract", "create a contract", "generate contract",
            "can you create contract", "can you analyze contract", "can you analyze or create contracts",
            "can you create or analyze contracts", "can you create or analyze contract"
        ]):
            response_text = """⚠️ I cannot create or analyze contracts.

Please use Chickle's Contract Analyzer instead:
For contract analysis, visit [Chickle's Contract Analyzer](https://chicklelegalcontractanalyzer.netlify.app).

## What I Can Help With

I can assist with legal case files related to:\n

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

        elif any(phrase in lower_query for phrase in [
            "what you can do", "what can you do", "how can you help", "your use",
            "your features", "how do you assist", "your work", "your capabilities",
            "your functions", "what are you", "help me with", "what services",
            "what's your use", "what do you do"
        ]):
            response_text = """## My Capabilities

I can assist with legal case files related to:


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

    # Final cleaning to ensure consistent formatting
    response_text = clean_markdown(response_text)

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)