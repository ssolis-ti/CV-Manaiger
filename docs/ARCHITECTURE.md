# 🏗️ System Architecture: CV-Manaiger

> **[CONTEXT: ARCHITECTURE]**
> This document describes the structural design, design patterns, and data flow of the CV-Manaiger backend.
> **Target Audience:** System Architects, Future AI Agents.

---

## 1. High-Level Design (The "Twin-Brain" System)

The system is designed as a **Linear Pipeline with a Facade**, but functionally operates as a "Twin-Brain" architecture:
1.  **Left Brain (Structure)**: `Schematron-8b`. Deterministic, fact-based, standardizing.
2.  **Right Brain (Enrichment)**: `Gemma-3-27b`. Creative, advisory, inferential.

### 1.1 The "Twin-JSON" Payload
Functionally, the system produces a split output to separate **Fact** from **Opinion**. This is the core architectural constraint.

```json
{
  "source_cv": {
    "id": "uuid-v4",
    "full_name": "Juan Perez",
    "skills": ["Python", "AWS"] // <-- Explicitly extracted FACTS
  },
  "enrichment": {
    "target_cv_id": "uuid-v4", // <-- Linked
    "market_signals": { "stack_detected": ["Django", "PostgreSQL"] }, // <-- Inferred
    "coach_feedback": { "tip": "Mention Terraform" } // <-- Opinion
  }
}
```

---

## 2. Component Design (Facade Pattern)

The entry point is **`cv_formatter/main.py` -> `CVProcessor`**.
It orchestrates 5 distinct sequential steps.

### Step 1: The Janitor (`etl/cleaner.py`)
*   **Role**: Normalization (NFKC), ASCII conversion, bullet standardization.
*   **Goal**: Reduce noise for the LLM context window.

### Step 2: The Surgeon (`etl/section_extractor.py`)
*   **Role**: Heuristic splitting (Regex).
*   **Goal**: Identify logical blocks. *Current Limitation: Does not classify document type (Roadmap Phase 6).*

### Step 3: The Structurer (`llm/tagger.py`)
*   **Model**: `inference-net/schematron-8b`
*   **Constraint**: "Non-Negotiable Rules" for Date/Skill extraction.
*   **Output**: Strict Pydantic `CVData`.

### Step 4: The Formatter (`formatter/json_formatter.py`)
*   **Role**: Serialization and schema validation.

### Step 5: The Coach (`enricher/engine.py`)
*   **Model**: `google/gemma-3-27b-it`
*   **Input**: JSON String (Not raw text). Efficient token usaage.
*   **Output**: Strict Pydantic `EnrichmentData`.

---

## 3. Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Facade (CVProcessor)
    participant Cleaner
    participant LLM_Structure (Schematron)
    participant LLM_Enrich (Gemma 3)
    participant FileSystem

    User->>Facade: Raw Text + Options
    Facade->>Cleaner: clean_text()
    Cleaner-->>Facade: normalized_text
    Facade->>LLM_Structure: tag_cv(normalized_text)
    
    note right of LLM_Structure: Extracts FACTS only.\nDates & Hard Skills must be explicit.
    
    LLM_Structure-->>Facade: CVData (Pydantic)
    Facade->>LLM_Enrich: enrich_cv(CVData JSON)
    
    note right of LLM_Enrich: Infers Stack, Role Fit.\nGenerate Coaching Tips.
    
    LLM_Enrich-->>Facade: EnrichmentData
    Facade->>FileSystem: Save _output.json & _INSIGHTS.json
    Facade-->>User: Twin-JSON Result
```

---

## 4. Key Decisions & Trade-offs

| Decision | Impact | Trade-off |
| :--- | :--- | :--- |
| **Facade Pattern** | Simplifies CLI/API integration. | Makes internal state harder to observe without logging. |
| **Twin-JSON** | Perfect separation of concerns (ATS vs Coaching). | Requires two files/objects to get full picture. |
| **Sync Execution** | Easy to debug/test. | Cannot scale to >10 concurrent requests (Needs Celery). |
| **Hard Truncation** | Prevents API 400 Errors. | Discards data on >32k char inputs (Long CVs fail gracefully). |

---

## 5. Directory Structure Map

```text
cv_formatter/
├── etl/                # [Deterministic] Regex & cleaning logic
├── llm/                # [AI Layer 1] Schematron/Stucture logic
├── enricher/           # [AI Layer 2] Gemma/Coach logic
├── formatter/          # [Schema] Data Definitions (Pydantic)
├── utils/              # [Shared] Logging, Token Counters
├── config.py           # [Env] Singleton configuration
└── main.py             # [Entry] Facade orchestration
```
