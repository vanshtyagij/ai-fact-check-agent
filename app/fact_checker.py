import json
import re
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2:3b"

SYSTEM_EXTRACT = """
You extract factual claims from documents for a fact-checking application.
Return ONLY valid JSON in this shape:
{"claims":[{"claim":"...", "context":"...", "type":"stat|date|financial|technical|scientific|other"}]}

Rules:
- Extract only specific, externally verifiable claims.
- Prioritize numbers, percentages, dates, rankings, financial figures,
  scientific/technical facts, and named factual assertions.
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

Definitions — follow these strictly:
- Verified: reliable evidence directly supports the claim AS WRITTEN, including any stated
  conditions such as "at standard atmospheric pressure", date, unit, population, or scope.
- Inaccurate: the claim has some truth or is close to correct, but is misleading, incomplete,
  outdated, imprecise, or materially wrong in wording/number. Use this for partial truth.
- False: reliable evidence directly contradicts the claim. Use this only when the evidence
  clearly says the opposite or demonstrates the claim is factually wrong.
- Unverified: the available search results do not provide enough reliable evidence to decide.
  NEVER call a claim False or Inaccurate merely because a search returned no useful source.

Important reasoning rules:
1. A lack of evidence is NOT evidence of falsity.
2. Check the exact wording and conditions. For example, "water boils at 100 C at standard
   atmospheric pressure" is supported by standard scientific references; pressure dependence
   does not make that conditional statement false.
3. If a search result directly supports the claim, prefer Verified even if the claim could be
   phrased with more detail.
4. If evidence directly contradicts the claim, use False.
5. If evidence supports part but not all of the claim, use Inaccurate.
6. If the search results are weak, irrelevant, contradictory without resolution, or empty,
   use Unverified rather than guessing.
7. Prefer primary/official/scientific sources and reputable institutions.
8. Confidence is an integer from 0 to 100 reflecting how strong the supplied evidence is for
   the verdict, not how confident you are in your writing.
9. Include only URLs that literally appear in the supplied search results.
10. Use 1-3 strongest sources. The source title should be the actual result title.
11. Keep assessment concise but explain the key evidence.
12. For Verified claims, real_fact can briefly restate the supported fact or condition.
13. For Unverified claims, real_fact should say that the available evidence was insufficient,
    not invent a correction.
"""


def _ollama_chat(prompt: str, model: str = DEFAULT_MODEL, system: str = "") -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            "Ollama is not running. Install Ollama, run it, then download a model "
            "with: ollama pull llama3.2:3b"
        ) from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama returned an error: {response.text[:500]}") from e
    data = response.json()
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
