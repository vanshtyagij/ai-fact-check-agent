import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash"

SYSTEM_EXTRACT = """
You extract factual claims from documents for a fact-checking application.
Return ONLY valid JSON in exactly this shape:
{"claims":[{"claim":"...","context":"...","type":"stat|date|financial|technical|scientific|other"}]}
Rules:
- Extract only specific, externally verifiable claims.
- Prioritize numbers, percentages, dates, rankings, financial figures, scientific/technical facts, and named factual assertions.
- Do not extract opinions, recommendations, or vague statements.
- Preserve the claim's meaning, conditions, units, dates, and numbers.
- Do not invent claims.
"""

SYSTEM_VERIFY = """
You are a careful, evidence-based fact-checking agent.
You are given web-search results for one claim. Use ONLY the supplied search results as evidence.
Do not invent sources, URLs, quotations, facts, or citations.
Return ONLY valid JSON in exactly this shape:
{
  "claim": "...",
  "status": "Verified|Inaccurate|False|Unverified",
  "assessment": "...",
  "real_fact": "...",
  "confidence": 0,
  "sources": [{"title":"...", "url":"..."}]
}
Definitions:
- Verified: reliable evidence directly supports the claim AS WRITTEN, including conditions such as date, unit, population, or scope.
- Inaccurate: the claim has some truth but is misleading, incomplete, outdated, imprecise, or materially wrong.
- False: reliable evidence directly contradicts the claim.
- Unverified: the supplied evidence is not enough to decide.
Important:
1. Lack of evidence is NOT evidence of falsity.
2. Check exact wording, numbers, dates, units and conditions.
3. Prefer primary, official, scientific and reputable sources.
4. Confidence must be an integer from 0 to 100.
5. Include only URLs that literally appear in the supplied search results.
6. Use 1-3 strongest sources.
7. For Unverified, do not invent a correction.
"""


def _get_gemini_api_key() -> str | None:
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    key = os.getenv("GEMINI_API_KEY")
    return key.strip() if key else None


def _gemini_chat(prompt: str, model: str = DEFAULT_MODEL, system: str = "") -> str:
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Open Streamlit Cloud > Manage app > Settings > Secrets and add GEMINI_API_KEY."
        )
    if not model or model.startswith("llama"):
        model = DEFAULT_MODEL
    full_prompt = f"{system.strip()}\n\n{prompt.strip()}".strip()
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    try:
        response = requests.post(
            GEMINI_URL.format(model=model),
            params={"key": api_key},
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Gemini API returned an error: {response.text[:1000]}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Gemini API request failed: {exc}") from exc
    try:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(f"Gemini returned an unexpected response: {data}") from exc


def _ollama_chat(prompt: str, model: str = DEFAULT_MODEL, system: str = "") -> str:
    # Kept for compatibility with the existing app.py import/calls.
    return _gemini_chat(prompt, model=model, system=system)


def _parse_json(text: str) -> Any:
    if not isinstance(text, str):
        raise ValueError("AI response was not text.")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
    raise ValueError("Gemini returned non-JSON output.")


def extract_claims(document_text: str, model: str = DEFAULT_MODEL, max_claims: int = 10) -> list[dict]:
    prompt = (
        f"Extract up to {max_claims} of the most important factual claims from this PDF text.\n\n"
        f"DOCUMENT:\n{document_text[:60000]}"
    )
    output = _gemini_chat(prompt, model=model, system=SYSTEM_EXTRACT)
    data = _parse_json(output)
    if isinstance(data, dict):
        claims = data.get("claims", [])
    elif isinstance(data, list):
        claims = data
    else:
        claims = []
    if not isinstance(claims, list):
        claims = []
    clean = []
    for item in claims:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim", "") or "").strip()
        if not claim:
            continue
        clean.append({
            "claim": claim,
            "context": str(item.get("context", "") or "").strip(),
            "type": str(item.get("type", "other") or "other").strip(),
        })
    return clean[:max_claims]


def web_search(query: str, max_results: int = 6) -> list[dict]:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Fact-Check-Agent)"}
    try:
        response = requests.get(url, params={"q": query}, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Web search failed: {exc}") from exc
    soup = BeautifulSoup(response.text, "html.parser")
    results, seen = [], set()
    for item in soup.select(".result"):
        link = item.select_one(".result__a")
        snippet = item.select_one(".result__snippet")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        href = link.get("href", "")
        text = snippet.get_text(" ", strip=True) if snippet else ""
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        results.append({"title": title, "url": href, "snippet": text})
        if len(results) >= max_results:
            break
    return results


def _search_claim(claim_text: str, context: str) -> list[dict]:
    queries = [
        f"{claim_text} {context}".strip(),
        f"{claim_text} fact official scientific source".strip(),
    ]
    merged, seen = [], set()
    for query in queries:
        for item in web_search(query, max_results=5):
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            merged.append(item)
            if len(merged) >= 8:
                return merged
    return merged


def _domain_name(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.") or "Source"
    except Exception:
        return "Source"


def verify_one(claim: dict, model: str = DEFAULT_MODEL) -> dict:
    claim_text = str(claim.get("claim", "") or "").strip()
    context = str(claim.get("context", "") or "").strip()
    search_results = _search_claim(claim_text, context)
    evidence_text = "\n\n".join(
        f"RESULT {i}: {r['title']}\nURL: {r['url']}\nSNIPPET: {r['snippet']}"
        for i, r in enumerate(search_results, 1)
    ) or "No search results were returned."
    prompt = f"""
Fact-check this claim using ONLY the supplied web-search results.

Claim: {claim_text}
Context from document: {context}
Claim type: {claim.get('type', 'other')}

WEB SEARCH RESULTS:
{evidence_text}

Compare the claim with the evidence word-for-word, including numbers, dates, units, conditions and scope.
Then return the required JSON only.
"""
    output = _gemini_chat(prompt, model=model, system=SYSTEM_VERIFY)
    parsed = _parse_json(output)
    if isinstance(parsed, list):
        result = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
    elif isinstance(parsed, dict):
        result = parsed
    else:
        result = {}

    valid_statuses = {"Verified", "Inaccurate", "False", "Unverified"}
    if result.get("status") not in valid_statuses:
        result["status"] = "Unverified"
    try:
        confidence = int(result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    result["confidence"] = max(0, min(100, confidence))
    result["claim"] = claim_text
    result["assessment"] = str(result.get("assessment", "") or "").strip()
    result["real_fact"] = str(result.get("real_fact", "") or "").strip()

    allowed = {r["url"]: r for r in search_results}
    clean_sources = []
    model_sources = result.get("sources", [])
    if not isinstance(model_sources, list):
        model_sources = []
    for source in model_sources:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url", "") or "").strip()
        if url in allowed:
            clean_sources.append({
                "title": str(source.get("title") or allowed[url]["title"]),
                "url": url,
            })
    if not clean_sources:
        clean_sources = [{"title": r["title"], "url": r["url"]} for r in search_results[:3]]
    result["sources"] = clean_sources[:3]
    for source in result["sources"]:
        source["source_name"] = _domain_name(source["url"])
    return result


def verify_claims(claims: list[dict], model: str = DEFAULT_MODEL) -> list[dict]:
    results = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        try:
            results.append(verify_one(claim, model=model))
        except Exception as exc:
            results.append({
                "claim": str(claim.get("claim", "")),
                "status": "Unverified",
                "assessment": f"Verification failed: {exc}",
                "real_fact": "",
                "confidence": 0,
                "sources": [],
            })
    return results
