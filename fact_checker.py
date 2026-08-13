import json
import r
SYSTEM_EXTRACT = """Extract the factual claims from the provided text.
Return only clear, verifiable factual claims."""
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests
import os
from bs4 import BeautifulSoup

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"
DEFAULT_MODEL = "gemini-3.6-flash"


def _ollama_chat(prompt: str, model: str = DEFAULT_MODEL, system: str = "") -> str:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it in Streamlit Secrets."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{system}\n\n{prompt}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            json=payload,
            timeout=180
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Gemini API error: {e}") from e

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected Gemini response: {data}")
    return data["message"]["content"]


def _parse_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise ValueError("The local AI returned non-JSON output.")


def extract_claims(document_text: str, model: str = DEFAULT_MODEL, max_claims: int = 10):
    prompt = (
        f"Extract up to {max_claims} of the most important factual claims from this PDF text.\n\n"
        f"DOCUMENT:\n{document_text[:60000]}"
    )
    output = _ollama_chat(prompt, model=model, system=SYSTEM_EXTRACT)
    data = _parse_json(output)
    return data.get("claims", [])[:max_claims]


def web_search(query: str, max_results: int = 6) -> list[dict]:
    """Free web search using DuckDuckGo HTML; no paid search API key required."""
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Fact-Check-Agent)"}
    try:
        r = requests.get(url, params={"q": query}, headers=headers, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Web search failed: {e}") from e

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    seen = set()
    for item in soup.select(".result"):
        a = item.select_one(".result__a")
        snippet = item.select_one(".result__snippet")
        if not a:
            continue
        title = a.get_text(" ", strip=True)
        href = a.get("href", "")
        text = snippet.get_text(" ", strip=True) if snippet else ""
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        results.append({"title": title, "url": href, "snippet": text})
        if len(results) >= max_results:
            break
    return results


def _search_claim(claim_text: str, context: str) -> list[dict]:
    """Use a couple of queries so exact wording does not cause avoidable no-result cases."""
    queries = [
        f"{claim_text} {context}".strip(),
        f"{claim_text} fact official scientific source".strip(),
    ]
    merged = []
    seen = set()
    for query in queries:
        for item in web_search(query, max_results=5):
            if item["url"] not in seen:
                seen.add(item["url"])
                merged.append(item)
            if len(merged) >= 8:
                return merged
    return merged


def _domain_name(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        return host or "Source"
    except Exception:
        return "Source"


def verify_one(claim: dict, model: str = DEFAULT_MODEL) -> dict:
    claim_text = claim.get("claim", "")
    context = claim.get("context", "")
    search_results = _search_claim(claim_text, context)

    evidence_text = "\n\n".join(
        f"RESULT {i}: {r['title']}\nURL: {r['url']}\nSNIPPET: {r['snippet']}"
        for i, r in enumerate(search_results, 1)
    )
    if not evidence_text:
        evidence_text = "No search results were returned."

    prompt = f"""
Fact-check this claim using the supplied web-search results.

Claim: {claim_text}
Context from document: {context}
Claim type: {claim.get('type', 'other')}

WEB SEARCH RESULTS:
{evidence_text}

First compare the claim word-for-word with the evidence, including conditions and scope.
Then choose exactly one status using the definitions in the system instructions.
Return the required JSON only.
"""
    output = _ollama_chat(prompt, model=model, system=SYSTEM_VERIFY)
    result = _parse_json(output)

    valid_statuses = {"Verified", "Inaccurate", "False", "Unverified"}
    status = result.get("status")
    if status not in valid_statuses:
        result["status"] = "Unverified"

    try:
        confidence = int(result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    result["confidence"] = max(0, min(100, confidence))
    result["claim"] = claim_text

    # Never let the model invent URLs. Keep only URLs that came from the search results.
    allowed = {r["url"]: r for r in search_results}
    clean_sources = []
    for source in result.get("sources", []) or []:
        url = source.get("url", "") if isinstance(source, dict) else ""
        if url in allowed:
            clean_sources.append({
                "title": source.get("title") or allowed[url]["title"],
                "url": url,
            })
    if not clean_sources:
        # Show the strongest returned search results even if the small local model omitted them.
        clean_sources = [
            {"title": r["title"], "url": r["url"]} for r in search_results[:3]
        ]
    result["sources"] = clean_sources[:3]

    # Add source-domain metadata for the UI/report without inventing a source.
    for source in result["sources"]:
        source["source_name"] = _domain_name(source["url"])

    return result


def verify_claims(claims: list[dict], model: str = DEFAULT_MODEL) -> list[dict]:
    return [verify_one(claim, model=model) for claim in claims]
