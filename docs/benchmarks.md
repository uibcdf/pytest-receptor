# Benchmarks y Ahorro de Tokens

Para validar cuantitativamente la eficiencia del modo `llm`, nuestra suite incluye un módulo de benchmarks que mide el número de tokens consumidos usando el codificador oficial de OpenAI `cl100k_base` (empleado por GPT-4 y modelos compatibles).

---

## Resultados Comparativos

La siguiente tabla muestra las métricas de tokens medidas en la suite de benchmarks bajo distintas casuísticas comunes de ejecución de pruebas:

| Escenario / Casuística | Salida Human (Tokens) | Salida LLM (Tokens) | Ahorro Promedio (%) |
| :--- | :---: | :---: | :---: |
| **Warnings Suite** (Deprecaciones) | 198 | 12 | **93.94%** |
| **Green Suite** (Éxito tradicional) | 99 | 12 | **87.88%** |
| **Cascade Failures** (Fallas comunes en 20 tests) | 1864 | 303 | **83.74%** |
| **Mixed States Suite** | 118 | 26 | **77.97%** |
| **Red Suite** (Fallo de aserción simple) | 312 | 163 | **47.76%** |
| **Multiple Failures** (Fallas de fixture + test) | 269 | 185 | **31.23%** |
| **Collection Error** (Error de importación) | 279 | 202 | **27.60%** |

---

## Análisis de los Resultados

* **Éxito (Ahorro > 85%):** En el ciclo diario de desarrollo (donde el 90% del tiempo las pruebas pasan), silenciar los entornos, cabeceras y progreso ahorra casi la totalidad de los tokens en cada ejecución, reduciendo la latencia de respuesta del agente de IA.
* **Fallas en Cascada (Ahorro > 80%):** Al agrupar fallos por firma e inyectar nombres abreviados de tests, evitamos repetir el mismo traceback 20 veces, protegiendo al agente de "ceguera de contexto" y ahorrando miles de tokens.
* **Fallas de aserción (Ahorro > 45%):** El ahorro es del 47% al eliminar la impresión del código fuente del test (el cual ya está indexado en el contexto del LLM) y conservar únicamente la aserción y los diffs estructurales de comparación.
