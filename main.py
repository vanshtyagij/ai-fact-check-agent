import json
import streamlit as st
from app.pdf_utils import extract_pdf_text
from app.fact_checker import DEFAULT_MODEL, extract_claims, verify_claims

st.set_page_config(page_title="Fact-Check Agent", page_icon="🔎", layout="wide")

st.title("🔎 Fact-Check Agent")
st.caption("Upload a PDF → extract factual claims → verify them with a free local AI model + web search.")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value=DEFAULT_MODEL)
    max_claims = st.slider("Maximum claims to verify", 3, 20, 10)
    st.info(
        "AI runs locally through Ollama. Web evidence is fetched with DuckDuckGo. "
        "No OpenAI API key or API credits are required."
    )

uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded:
    if st.button("🚀 Fact-check PDF", type="primary"):
        try:
            with st.spinner("Extracting PDF text..."):
                text = extract_pdf_text(uploaded)

            if not text.strip():
                st.error("No readable text was found in this PDF.")
                st.stop()

            with st.expander("Extracted PDF text"):
                st.text(text[:12000])

            with st.spinner("Identifying factual claims with local AI..."):
                claims = extract_claims(text, model=model, max_claims=max_claims)

            if not claims:
                st.warning("No specific factual/statistical claims were detected.")
                st.stop()

            st.success(f"Found {len(claims)} claims. Verifying against web data...")

            results = verify_claims(claims, model=model)

            verified = sum(r.get("status") == "Verified" for r in results)
            inaccurate = sum(r.get("status") == "Inaccurate" for r in results)
            false = sum(r.get("status") == "False" for r in results)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Claims", len(results))
            c2.metric("✅ Verified", verified)
            c3.metric("⚠️ Inaccurate", inaccurate)
            c4.metric("❌ False", false)

            st.divider()

            for i, result in enumerate(results, start=1):
                status = result.get("status", "False")
                icon = {"Verified": "✅", "Inaccurate": "⚠️", "False": "❌"}.get(status, "❓")
                with st.container(border=True):
                    st.subheader(f"{icon} Claim {i}: {status}")
                    st.write("**Claim:**", result.get("claim", ""))
                    st.write("**Assessment:**", result.get("assessment", ""))
                    if result.get("real_fact"):
                        st.write("**Correct / current fact:**", result["real_fact"])

                    sources = result.get("sources", [])
                    if sources:
                        st.write("**Sources:**")
                        for source in sources:
                            title = source.get("title") or source.get("url") or "Source"
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"- [{title}]({url})")
                            else:
                                st.write(f"- {title}")

            st.download_button(
                "⬇️ Download JSON report",
                data=json.dumps(results, indent=2, ensure_ascii=False),
                file_name="fact_check_report.json",
                mime="application/json",
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)
else:
    st.markdown("""
### How it works
1. Upload a PDF containing statistics, dates, financial figures, or technical claims.
2. The local AI extracts specific claims.
3. Each claim is checked using web search.
4. Results are classified as **Verified**, **Inaccurate**, or **False**.
5. Evidence links and the corrected fact are shown where available.

> **Important:** This version runs the AI locally. It still needs an internet connection for web search.
""")
