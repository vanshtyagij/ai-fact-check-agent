# AI Fact-Check Agent

An AI-powered fact-checking application that extracts factual claims from PDF documents, searches the web for supporting evidence, and evaluates each claim using a locally running LLM through Ollama.

## Overview

The AI Fact-Check Agent is designed to help users identify potentially incorrect or misleading information in PDF documents.

The application:

1. Accepts a PDF document.
2. Extracts its text.
3. Identifies factual claims.
4. Searches the web for relevant evidence.
5. Uses a local AI model to evaluate the evidence.
6. Displays the verdict, explanation, correct fact, confidence score, and source information.

## Key Features

- 📄 PDF document upload
- 🔎 Automatic factual-claim extraction
- 🌐 Web-based evidence search
- 🤖 Local AI verification using Ollama
- 🟢 Verified claims
- 🟡 Inaccurate claims
- 🔴 False claims
- ⚪ Unverified claims
- 📊 Confidence score
- 📝 Explanation and corrected fact
- 🔗 Source name and clickable source URL
- 💻 Local AI processing without OpenAI API credits

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Streamlit | Web interface |
| Ollama | Local AI model runtime |
| Llama 3.2 3B | Local language model |
| DuckDuckGo | Web evidence search |
| pypdf | PDF text extraction |

## System Workflow

```text
PDF Upload
     ↓
PDF Text Extraction
     ↓
Claim Extraction
     ↓
Web Evidence Search
     ↓
Evidence Collection
     ↓
Local Ollama AI
     ↓
Claim Evaluation
     ↓
Final Fact-Check Result
Verdict Categories
🟢 Verified
Reliable evidence supports the claim.
🟡 Inaccurate
The claim is partially incorrect, misleading, or needs correction.
🔴 False
Reliable evidence directly contradicts the claim.
⚪ Unverified
Sufficient reliable evidence could not be found. This does not automatically mean the claim is false.
Installation
1. Install Ollama
Install Ollama and make sure the Ollama service is running.
Download the required model:
ollama pull llama3.2:3b
Test the model:
ollama run llama3.2:3b
After confirming that the model responds, press:
Ctrl + C
to exit.
2. Create and activate a virtual environment
python -m venv .venv
Windows:
.venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Run the application
streamlit run app.py
Open the local URL shown by Streamlit, usually:
http://localhost:8501
Project Structure
ai-fact-check-agent/
│
├── .streamlit/
│   └── config.toml
│
├── app/
│   └── supporting project files
│
├── sample_data/
│   ├── sample PDF
│   └── sample text file
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── DEMO_VIDEO_SCRIPT.md
└── SUBMISSION_TEMPLATE.txt
Sample Data
The sample_data directory contains sample documents that can be used to test the application.
Local AI
This project uses Ollama and a locally running Llama model instead of the OpenAI API.
Therefore:
No OpenAI API key is required.
No OpenAI API credits are required.
AI inference is performed locally.
Internet access is still required for web evidence searches.
Important Limitation
The current implementation uses an Ollama model running locally on the user's computer.
Therefore, a standard cloud deployment cannot directly access the Ollama model running on a personal laptop.
For cloud deployment, a cloud-accessible AI inference backend or hosted model would be required.
Limitations
Verification quality depends on the quality and availability of web evidence.
The local 3B model has limited reasoning capability compared with larger models.
Some complex claims may require manual verification.
Current web evidence requires an active internet connection.
AI-generated verdicts should be treated as decision support rather than absolute truth.
Future Scope
Possible improvements include:
Larger and more capable local language models
Improved source ranking
Multi-language fact checking
News article verification
Image and video fact checking
Historical claim verification
Better confidence calibration
Database of previously verified claims
Cloud-compatible AI inference
License
