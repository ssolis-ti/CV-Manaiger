# Auditoría Arquitectónica: Las 7 Leyes Herméticas

Este documento analiza el estado actual de **CV-Manaiger** bajo el prisma de las 7 Leyes Universales aplicadas a la ingeniería de software.

## 1. Ley del Mentalismo (Todo es Mente)
> *"El universo es una creación mental."* → **El código es la manifestación de un modelo mental.**

*   **Estado Actual**:
    *   ✅ **Fuerte**: El uso de Pydantic (`json_formatter.py`) define un modelo mental estricto de los datos antes de procesarlos.
    *   ✅ **Claro**: El patrón Fachada (`main.py`) abstrae la complejidad, reflejando un modelo mental de "Caja Negra" para el consumidor.
*   **Brecha**:
    *   El "Prompt" (`tagger.py`) contiene la lógica "blanda" o psicológica del reclutador, pero está "hardcodeado" dentro de la clase lógica.
*   **Sugerencia**:
    *   Extraer el System Prompt a un archivo de configuración o constante separada (`prompts.py`). Esto separa la "Intención" (Prompt) de la "Mecánica" (Código).

## 2. Ley de Correspondencia (Como es arriba, es abajo)
> *"Lo micro refleja lo macro."*

*   **Estado Actual**:
    *   ✅ **Consistencia**: La estructura de carpetas (`etl`, `llm`, `formatter`) corresponde a los pasos del pipeline lógico.
    *   ✅ **Manejo de Errores**: Se usa `try/except` en capas bajas y altas.
*   **Sugerencia**:
    *   Estandarizar las respuestas de error. Actualmente, si falla el ETL, el error explota hacia arriba. Deberíamos tener un objeto `PipelineResult` que encapsule éxito/fallo de forma homogénea en todas las capas.

## 3. Ley de Vibración (Todo se mueve)
> *"Nada descansa, todo fluctúa."*

*   **Estado Actual**:
    *   ✅ **Resiliencia**: El uso de `tenacity` reconoce que las APIs externas (OpenAI/Inference) fallan y fluctúan.
    *   ⚠️ **Observabilidad**: Tenemos logs estáticos, pero no medimos el "pulso" (tiempo de ejecución por etapa).
*   **Sugerencia**:
    *   Implementar métricas de tiempo (`Start` -> `End`) en los logs para "sentir" la vibración del sistema (latencia).

## 4. Ley de Polaridad (Los opuestos son grados)
> *"Todo tiene dos polos."*

*   **Estado Actual**:
    *   **Rigidez vs Flexibilidad**:
        *   *Rigidez*: Pydantic forcejea una estructura estricta.
        *   *Flexibilidad*: Regex en `cleaner.py` es permisivo.
    *   ✅ **Balance**: El sistema acepta caos (Input raw) pero entrega orden (Output JSON).
*   **Sugerencia**:
    *   Mantener este balance. No hacer el Regex demasiado estricto (rechazaría CVs válidos) ni el Pydantic demasiado laxo (rompería el Frontend).

## 5. Ley del Ritmo (Ciclos y Flujo)
> *"Todo fluye y refluye."*

*   **Estado Actual**:
    *   Estamos en el final de un ciclo de **Creación (MVP)**.
    *   Toca entrar en un ciclo de **Estabilización** antes de la **Expansión (Frontend)**.
*   **Sugerencia**:
    *   Congelar las "features" del Backend ahora. No añadir más lógica de negocio hasta conectar el Frontend. Respetar el ritmo evita deuda técnica.

## 6. Ley de Causa y Efecto (Nada es casualidad)
> *"Toda causa tiene su efecto."*

*   **Estado Actual**:
    *   ✅ **Trazabilidad**: Los logs con *timestamps* permiten reconstruir la cadena causal de un error.
    *   ✅ **Determinismo**: `cleaner.py` asegura que el mismo input sucio siempre produzca el mismo input limpio para la IA (reduciendo la variabilidad "azarosa").
*   **Sugerencia**:
    *   Añadir un `correlation_id` o `run_id` si el sistema escala a procesar múltiples CVs en paralelo (API web), para no mezclar logs.

## 7. Ley de Generación (Masculino y Femenino)
> *"La creación surge de la tensión."*

*   **Estado Actual**:
    *   **Femenino (Recepción/Creatividad)**: El `LLMTagger` interpreta, "siente" el estilo y deduce seniority de forma abstracta.
    *   **Masculino (Estructura/Ley)**: El `JSONFormatter` impone reglas, esquemas y tipos estrictos.
*   **Sugerencia**:
    *   Esta tensión es el núcleo del producto. Asegurar que la IA (Creativa) nunca rompa la Estructura (Ley). El uso de `response_format` en la API es la implementación técnica perfecta de esta ley.
