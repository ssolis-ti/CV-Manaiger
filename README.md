# CV-Manaiger 📄✨

**Sistema Inteligente de Gestión y Optimización de CVs.**
Transforma currículums desordenados en datos estructurados (JSON) listos para Inteligencia Artificial.

---

---

## 📚 Documentation (The "Brain")

**[MANDATORY CHECKPOINT]**: [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) (Read before continuing)

Detailed documentation is available in the `docs/` folder:
*   **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Twin-JSON Design, Data Flow, Facade Pattern.
*   **[AI_CONTEXT.md](docs/AI_CONTEXT.md)**: System Prompts, Models (Schematron vs Gemma), and Resilience.
*   **[WORKFLOWS.md](docs/WORKFLOWS.md)**: How to run, debug, and test (SOPs).

---

## 🚀 Quickstart (Guía Rápida)

Sigue estos pasos para poner en marcha el backend de Python en menos de 5 minutos.

### 1. Requisitos Previos

*   **Python 3.10+** instalado.
*   Una **API Key de OpenAI** (necesitas saldo/crédito disponible).
*   Git.

### 2. Instalación

Clona el repositorio y entra en la carpeta:

```bash
git clone https://github.com/ssolis-ti/CV-Manaiger.git
cd CV-Manaiger
```

Crea y activa un entorno virtual (recomendado para no ensuciar tu sistema):

**En Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**En Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

### 3. Configuración

El sistema necesita tu clave de OpenAI para4.  **Configura el entorno**:
    Copia el archivo de ejemplo y configura tu API Key (OpenAI o Inference.net):
    ```powershell
    copy .env.example .env
    # Edita .env con tu clave
    ```

5.  **Ejecuta la Demo**:
    ```powershell
    python run_demo.py
    ```
    *   Selecciona **Opción 1** para pegar automáticamente desde el portapapeles.
    *   O selecciona **Opción 2** para pegar manualmente.
    OPENAI_API_KEY=sk-tu-clave-secreta-aqui...
    OPENAI_MODEL=gpt-4o-mini  # Puedes cambiarlo a gpt-4o si prefieres
    ```

### 4. ¡Pruébalo!

Hemos incluido un script de demostración interactivo.

Ejecuta el siguiente comando:

```bash
python run_demo.py
```

1.  La terminal te pedirá que pegues el texto de un CV.
2.  Copia cualquier texto de CV (desordenado, con bullets raros, etc.).
3.  Pégalo en la terminal.
4.  Presiona **Enter**, y luego **Ctrl+Z** (en Windows) o **Ctrl+D** (en Linux/Mac) y luego **Enter** otra vez para indicar que terminaste de escribir.

✨ **Verás la magia:** El sistema limpiará el texto, lo analizará con IA y te devolverá un **JSON perfecto** con secciones, habilidades detectadas y métricas de impacto.

---

## 📂 Estructura del Proyecto

Para los curiosos, así está organizado el "cerebro":

## Architecture 🏗️
The system follows a modular **Facade Pattern**.

```mermaid
graph TD
    User([User / CLI]) --> Facade[CVProcessor (Main)]
    Facade --> ETL_Clean[Cleaner (Regex)]
    Facade --> ETL_Split[Extractor (Heuristics)]
    Facade --> Brain[LLMTagger (AI)]
    Facade --> Format[JSON Formatter (Pydantic)]
    
    ETL_Clean --> ETL_Split
    ETL_Split --> Brain
    Brain -->|Draft Data| Format
    Format -->|Valid JSON| Output[(Files)]
    
    subgraph Observability
    Logger[Rich Logger] -.-> Facade
    end
```

*   `cv_formatter/main.py`: **El Jefe (Facade)**. Conecta todas las piezas. Si vas a usar esto en tu código, importa la clase `CVProcessor` de aquí.
*   `cv_formatter/etl/`: **Limpieza**. Se encarga de quitar basura y normalizar el texto antes de que la IA lo toque.
*   `cv_formatter/llm/`: **Inteligencia**. Aquí vive el `tagger.py` que habla con OpenAI. Incluye reintentos automáticos y control de costos.
*   `cv_formatter/formatter/`: **Orden**. Define la estructura exacta del JSON final usando Pydantic.

## 🧪 Tests

Si quieres verificar que todo funciona correctamente a nivel de código:

```bash
pytest
```
Esto ejecutará las pruebas automáticas de limpieza y extracción.
