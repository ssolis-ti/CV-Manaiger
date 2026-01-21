# ⚙️ Operational Workflows: CV-Manaiger

> **[CONTEXT: WORKFLOWS]**
> This document details the standard operating procedures (SOPs) for running, debugging, and testing the system.
> **Target Audience:** Developers, QA, End Users.

---

## 1. Environment Setup (First Run)

### Prerequisites
*   Python 3.10+
*   Git

### Steps
1.  **Clone & Install**:
    ```powershell
    git clone <repo>
    cd CV-Manaiger
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Configuration**:
    *   Duplicate `.env.example` -> `.env`.
    *   Add your API Keys (`OPENAI_API_KEY`, optionally `API_KEY_ENRICH`).

---

## 2. Daily Usage (The CLI)

To process CVs manually:
```powershell
python run_demo.py
```
**Options**:
1.  **Clipboard (Recommended)**: Copy any text (PDF content, Word doc), then select Option 1.
2.  **Manual**: Paste explicit text.

**Outputs**:
*   Location: `output/CV_{Name}_{Date}.json` (Facts)
*   Location: `output/CV_{Name}_{Date}_INSIGHTS.json` (Advice)
*   Location: `output/CV_{Name}_{Date}.md` (Readable)

---

## 3. Development & Testing (QA)

### 3.1 Integrity Checks (Mandatory)
Before pushing any code, run the integrity suite:
```powershell
pytest tests/test_integrity.py
```
✅ **Pass Criteria**:
*   Dates extracted if years present.
*   Skills extracted if keywords present.
*   No "coaching language" in Source CV.

### 3.2 Resilience Test
If you change the Extraction Logic (Schematron), verify that Enrichment still works on bad data:
```powershell
python scripts/debug_enrichment.py
```
*   Expect: `[VERDICT] ✅ SUCCESS`.

---

## 4. Troubleshooting

### Incident: "Enrichment returned None"
*   **Cause**: The API call to Gemma 3 failed or timed out.
*   **Check**: `logs/cv_processing_YYYY-MM-DD.log`.
*   **Fix**: Check `API_KEY_ENRICH` or Credit Balance.

### Incident: "400 Bad Request"
*   **Cause**: Input text too long (>32k chars).
*   **Fix**: The codified Truncation Logic (`llm/tagger.py`) should catch this. Check if the limit was manually disabled.
