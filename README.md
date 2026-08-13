
content = """# AI Fact-Check Agent

An AI-powered fact-checking application that extracts factual claims from PDF documents, searches the web for supporting evidence, and evaluates each claim using a locally running AI model through Ollama.

## Overview

The AI Fact-Check Agent helps users identify potentially incorrect or misleading information in PDF documents.

### How It Works

1. PDF Upload
2. PDF Text Extraction
3. Claim Extraction
4. Web Evidence Search
5. Evidence Collection
6. Local Ollama AI Analysis
7. Claim Evaluation
8. Final Fact-Check Result

## Key Features

- PDF document upload
- Automatic factual-claim extraction
- Web-based evidence search
- Local AI verification using Ollama
- Verified, inaccurate, false, and unverified verdicts
- Confidence score
- Explanation and corrected fact
- Source name and clickable source URL
- Local AI processing without OpenAI API credits

## Verdict Categories

### 🟢 Verified

Reliable evidence supports the claim.

### 🟡 Inaccurate

The claim is partially incorrect, misleading, or needs correction.

### 🔴 False

Reliable evidence directly contradicts the claim.

### ⚪ Unverified

Sufficient reliable evidence could not be found. This does not automatically mean the claim is false.

## Installation

### 1. Install Ollama

Install Ollama and make sure the Ollama service is running.

Required model:

ollama pull llama3.2:3b

### 2. Create and Activate a Virtual Environment

Windows:

python -m venv .venv

.venv\\Scripts\\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Run the Application

streamlit run app.py

Open the local URL shown by Streamlit, usually:

http://localhost:8501

## Project Structure

- .streamlit/ — Streamlit configuration directory
- .streamlit/config.toml — Streamlit theme configuration
- app/ — Supporting application files
- sample_data/ — Sample documents for testing
- app.py — Main Streamlit application
- requirements.txt — Python dependencies
- README.md — Project documentation
- .gitignore — Git ignored files and folders
- DEMO_VIDEO_SCRIPT.md — Demo video script
- SUBMISSION_TEMPLATE.txt — Submission-related template

## Technology Stack

- Python — Application development
- Streamlit — User interface
- Ollama — Local AI inference
- Llama 3.2 3B — Local language model
- Web Search — Evidence retrieval
- PDF Processing — Text extraction

## Important Limitation

The current implementation uses an Ollama model running locally on the user's computer. A standard cloud deployment cannot directly use a local Ollama instance. Cloud deployment would require a cloud-accessible AI inference backend or hosted model.

## Limitations

- Verification quality depends on the quality and availability of web evidence.
- The local 3B model has limited reasoning capability compared with larger models.
- Complex claims may require manual verification.
- Current web evidence requires an active internet connection.
- AI-generated verdicts should be treated as decision support rather than absolute truth.

## Future Scope

- Use larger and more capable local language models.
- Improve source ranking and reliability assessment.
- Enable fact checking across multiple languages.
- Add dedicated news article verification.
- Extend fact checking beyond PDF and text content.
- Add image and video verification.
- Support historical claim verification.
- Improve confidence-score reliability.
- Maintain a database of previously verified claims.
- Add cloud-compatible AI inference.

## License

Developed as part of a Product Management Trainee assessment project.
"""


