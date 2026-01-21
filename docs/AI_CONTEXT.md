# 🧠 AI Context & Mastery: CV-Manaiger

> **[CONTEXT: AI_MASTERY]**
> This document explains the Prompt Engineering, Model Selection, and Token Logic used in the backend.
> **Target Audience:** Prompt Engineers, AI Agents, Backend Developers.

---

## 1. Model Strategy (Twin-Model)

| Role | Model | Provider | Why? |
| :--- | :--- | :--- | :--- |
| **Structure** | `inference-net/schematron-8b` | Inference.net | Precision, JSON-following capability, low hallucination. |
| **Enrichment** | `google/gemma-3-27b-it` | Inference.net | Creative reasoning, Spanish fluency, high "Coach" capability. |

---

## 2. System Prompts (The "Golden Rules")

### 2.1 Prompt 1: The Structurer (`llm/tagger.py`)
> **Goal:** Extract FACTS. Do not invent.
> **Key Mechanism:** "Non-Negotiable Rules".

**Crucial Instructions:**
*   **Dates**: `If a date range exists... MUST assign start_date and end_date.`
*   **Skills (Extraction)**: `Any skill explicitly mentioned... MUST be added to CVData.skills.`
*   **Skills (Inference)**: `Inferred skills go ONLY to metadata or enrichment.`

*See `cv_formatter/llm/tagger.py` for full text.*

### 2.2 Prompt 2: The Coach (`enricher/engine.py`)
> **Goal:** Generate INSIGHTS. Be opinionated.
> **Key Mechanism:** "Persona Injection" (Technical Recruiter).

**Crucial Instructions:**
*   **Language**: `OUTPUT MUST BE IN SPANISH (ES-LATAM).`
*   **Stack vs Tools**: Distinguish Core Tech (Python) from SaaS (Jira).
*   **Missing Skills**: " What is missing for the NEXT level?"

*See `cv_formatter/enricher/engine.py` for full text.*

---

## 3. Resilience Mechanisms

### 3.1 Token Safety
*   **Limit**: Input text is truncated at **32,000 characters**.
*   **Why**: Prevent `400 Bad Request` from the API provider.
*   **Log**: Generates a `[TRUNCATED_BY_SYSTEM]` marker in logs.

### 3.2 Resilience Test (`scripts/debug_enrichment.py`)
We verified that if Schematron fails to extract skills (returning `[]`), Gemma 3 **can still read the raw text** and identify the stack. This dual-layer approach acts as a Safety Net.

---

## 4. Configuration (Env Vars)

To change models, update `.env`:
```ini
# MODELO 1: Structure (Facts)
MODEL_STRUCTURE=inference-net/schematron-8b

# MODELO 2: Enrichment (Opinions)
MODEL_ENRICH=google/gemma-3-27b-it
```
