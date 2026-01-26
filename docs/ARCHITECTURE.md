# 🏗️ CV Manaiger: Arquitectura del Sistema

**Versión:** 3.0 (One-Shot Semantic Structurer)  
**Fecha:** 2026-01-26  
**Estado:** Stable  

---

## 📋 Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Flujo de Datos](#2-flujo-de-datos)
3. [Módulos del Sistema](#3-módulos-del-sistema)
4. [Schemas de Datos](#4-schemas-de-datos)
5. [Advertencias y Limitaciones](#5-advertencias-y-limitaciones)

---

## 1. Visión General

CV Manaiger es un sistema de extracción de información de CVs que utiliza LLMs para convertir texto no estructurado en JSON estructurado.

### Problema Resuelto
- CVs copiados de PDFs llegan con formato roto (columnas, fechas desplazadas).
- El sistema debe manejar inputs "salvajes" sin estructura visible.

### Solución Implementada
**One-Shot Semantic Structurer (V3):**
- **Single Pass (LLM):** Extrae la estructura completa (Experiencia, Educación, Skills) en una sola llamada usando `response_format` estricto (Pydantic).
- **Date Recovery Heuristic:** Proceso determinístico post-LLM para recuperar fechas en formatos columnares difíciles.

---

## 2. Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                      ENTRADA: Texto Crudo                       │
│   (Copy-paste de PDF, LinkedIn, Word - potencialmente caótico)  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 0: TRIAGE                                                 │
│  Archivo: cv_formatter/etl/triage.py                            │
│  Función: Valida si el texto es un CV válido                    │
│  ⚠️ ADVERTENCIA: Rechaza textos muy cortos o sin keywords       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 0.5: ATS CHECK                                            │
│  Archivo: cv_formatter/etl/ats_checker.py                       │
│  Función: Evalúa parsabilidad ATS (score 0-100)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: CLEANING                                               │
│  Archivo: cv_formatter/etl/cleaner.py                           │
│  Función: Normaliza Unicode, elimina emojis, estandariza bullets│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: SEMANTIC STRUCTURER (One-Shot)                         │
│  Archivo: cv_formatter/etl/semantic_structurer.py               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ extract_structure() - LLM (Schematron-8b / Gemma)       │   │
│  │ - Input: Texto Limpio                                   │   │
│  │ - Output: Objeto ExtractedCV (Pydantic)                 │   │
│  │ - Contexto: Agrupa "Company + Role + Dates" nativamente │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2.5: COLUMNAR DATE RECOVERY (Opcional)                    │
│  Archivo: cv_formatter/main.py (Logica in-line)                 │
│  Función: Si faltan fechas, busca patrones regex en el texto    │
│  y las asigna secuencialmente (Heurística de lectura).          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CONVERT & ENRICH                                       │
│  Archivo: cv_formatter/main.py                                  │
│  Función: Convierte a CVData y ejecuta Enrichment (Gemma 3)     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SALIDA: Twin-JSON                          │
│  {                                                              │
│    "source_cv": { ... datos extraídos ... },                    │
│    "enrichment": { ... insights opcionales ... }                │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Módulos del Sistema

### 3.1 Entry Points

| Archivo | Descripción |
|---------|-------------|
| `run_demo.py` | CLI interactiva con Rich. Punto de entrada para usuarios. |
| `cv_formatter/main.py` | Orquestador principal (`CVProcessor`). Facade Pattern. |

### 3.2 ETL & LLM

| Archivo | Rol | LLM Calls |
|---------|-----|-----------|
| `etl/triage.py` | Valida input | 0 |
| `etl/ats_checker.py` | Score ATS | 0 |
| `etl/cleaner.py` | Limpia texto | 0 |
| `etl/semantic_structurer.py` | **One-Shot Structurer** (Core) | 1 |
| `etl/date_preprocessor.py` | Regex de fechas (Recovery) | 0 |

### 3.3 Enricher

| Archivo | Rol | LLM Calls |
|---------|-----|-----------|
| `enricher/engine.py` | Insights con Gemma 3 | 1 |

---

## 4. Schemas de Datos

### 4.1 Output del Structurer

```python
class ExtractedCV(BaseModel):
    full_name: Optional[str]
    professional_summary: Optional[str]
    experience: List[ExperienceItem]
    education: List[EducationItem]
    skills: TechnicalSkills
```

### 4.2 Output Final

```python
class CVData(BaseModel):
    id: str
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    summary: Optional[str]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    certifications: List[CertificationEntry]
    skills: SkillSection
    ats_analysis: Optional[ATSAnalysis]
    metadata: Optional[AnalysisMetadata]
```

---

## 5. Advertencias y Limitaciones

### ⚡ Conocidas

- **Costos LLM:** El One-Shot envía todo el texto del CV en una sola llamada. Para CVs muy largos (>4 páginas), podría truncarse o ser costoso.
- **Enrichment Opcional:** Si el modelo de enrichment falla, el campo `enrichment` será `null`, pero `source_cv` persiste.
- **Fechas Columnares:** La heurística de recuperación asume orden cronológico descendente visual. Si el PDF tiene un layout muy complejo (tablas anidadas), podría asignar fechas incorrectamente.
