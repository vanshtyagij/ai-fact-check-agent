AI Fact-Check Agent
An AI-powered fact-checking application that extracts factual claims from PDF documents, searches the web for supporting evidence, and evaluates each claim using a locally running LLM through Ollama.

Overview
The AI Fact-Check Agent is designed to help users identify potentially incorrect or misleading information in PDF documents.

The application:

Accepts a PDF document.
Extracts its text.
Identifies factual claims.
Searches the web for relevant evidence.
Uses a local AI model to evaluate the evidence.
Displays the verdict, explanation, correct fact, confidence score, and source information.
Key Features
📄 PDF document upload
🔎 Automatic factual-claim extraction
🌐 Web-based evidence search
🤖 Local AI verification using Ollama
🟢 Verified claims
🟡 Inaccurate claims
🔴 False claims
⚪ Unverified claims
📊 Confidence score
📝 Explanation and corrected fact
🔗 Source name and clickable source URL
💻 Local AI processing without OpenAI API credits
Technology Stack
Technology	Purpose
Python	Application development
Streamlit	Web interface
Ollama	Local AI model runtime
Llama 3.2 3B	Local language model
DuckDuckGo	Web evidence search
pypdf	PDF text extraction
System Workflow
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

## Verdict Categories

| Verdict | Meaning |
|---|---|
| 🟢 **Verified** | Reliable evidence supports the claim. |
| 🟡 **Inaccurate** | The claim is partially incorrect, misleading, or needs correction. |
| 🔴 **False** | Reliable evidence directly contradicts the claim. |
| ⚪ **Unverified** | Sufficient reliable evidence could not be found. This does not automatically mean the claim is false. |

## Installation

### 1. Install Ollama

Install Ollama and make sure the Ollama service is running.

Download the required model:

```bash
ollama pull llama3.2:3b

## Project Structure

| Component | Description |
|---|---|
| `.streamlit/` | Streamlit configuration directory |
| `.streamlit/config.toml` | Streamlit theme configuration |
| `app/` | Supporting application files |
| `sample_data/` | Sample documents for testing |
| `sample_data/sample PDF` | Sample PDF document |
| `sample_data/sample text file` | Sample text document |
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `README.md` | Project documentation |
| `.gitignore` | Git ignored files and folders |
| `DEMO_VIDEO_SCRIPT.md` | Demo video script |
| `SUBMISSION_TEMPLATE.txt` | Submission-related template |

## Sample Data

| Item | Details |
|---|---|
| Sample PDF | Used for testing PDF-based fact checking |
| Sample Text File | Used as sample textual input |
| Location | `sample_data/` |

## Local AI

This project uses Ollama and a locally running Llama model instead of the OpenAI API.

| Feature | Details |
|---|---|
| OpenAI API Key | Not required |
| OpenAI API Credits | Not required |
| AI Inference | Performed locally using Ollama |
| Web Search | Requires an active internet connection |
| AI Model | Llama 3.2 3B |

## Important Limitation

| Limitation | Details |
|---|---|
| Local Ollama | The current implementation uses an Ollama model running locally on the user's computer. |
| Cloud Deployment | A standard cloud deployment cannot directly use the Ollama model running on a personal laptop. |
| Cloud AI Requirement | A cloud-accessible AI inference backend or hosted model would be required for cloud deployment. |

## Limitations

| Limitation | Description |
|---|---|
| Web Evidence | Verification quality depends on the quality and availability of web evidence. |
| Local Model | The local 3B model has limited reasoning capability compared with larger models. |
| Complex Claims | Some complex claims may require manual verification. |
| Internet | Current web evidence requires an active internet connection. |
| AI Verdicts | AI-generated verdicts should be treated as decision support rather than absolute truth. |

## Future Scope

| Improvement | Description |
|---|---|
| Larger AI Models | Use larger and more capable local language models. |
| Source Ranking | Improve ranking and reliability assessment of sources. |
| Multi-language Support | Enable fact checking across multiple languages. |
| News Verification | Add dedicated news article verification. |
| Image & Video Verification | Extend fact checking beyond PDF/text content. |
| Historical Verification | Support verification of historical claims. |
| Confidence Calibration | Improve confidence-score reliability. |
| Claim Database | Maintain a database of previously verified claims. |
| Cloud AI | Support cloud-compatible AI inference. |

## License

| Information | Details |
|---|---|
| Project Type | Product Management Trainee Assessment |
| License | Developed as part of the assessment project |
