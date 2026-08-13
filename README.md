# 🔎 Fact-Check Agent — Free Local AI Version

This version removes the OpenAI API dependency. It uses:

- **Ollama** for a free local AI model
- **DuckDuckGo HTML search** for web evidence
- **Streamlit** for the UI
- **pypdf** for PDF text extraction

No OpenAI API key or OpenAI API credits are required.

## 1. Install Ollama

Install Ollama from its official website and make sure the Ollama app/service is running.

Then open Command Prompt or PowerShell and download a model:

```bash
ollama pull llama3.2:3b
```

Check that it works:

```bash
ollama run llama3.2:3b
```

Press `Ctrl+C` after confirming it responds.

> If your PC has enough RAM, you can use a larger model such as `llama3.1:8b` for better reasoning. Change the model name in the Streamlit sidebar.

## 2. Install the project

Create/activate your Python virtual environment, then:

```bash
pip install -r requirements.txt
```

## 3. Run the app

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## 4. How this version works

```text
PDF
 │
 ▼
pypdf text extraction
 │
 ▼
Ollama local AI
 │
 ▼
Specific factual claims
 │
 ▼
DuckDuckGo web search
 │
 ▼
Search snippets + URLs
 │
 ▼
Ollama local AI
 │
 ▼
Verified / Inaccurate / False
```

## Important limitation

The AI is local and free, but **web search still needs an internet connection**. DuckDuckGo search is used without a paid search API key.

This version is intended for **local Windows use**. A Streamlit Cloud deployment cannot directly use an Ollama model running on your own laptop.

## If Ollama is not running

You may see an error saying:

```text
Ollama is not running
```

Start Ollama and run the app again.

## If you want to use a different model

Examples:

```bash
ollama pull llama3.2:3b
ollama pull llama3.1:8b
```

Then type the installed model name into the **Ollama model** field in the sidebar.
