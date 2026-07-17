# Guía de Uso

`pytest-receptor` se integra de forma transparente en tus comandos habituales de pytest a través del flag `--receptor`.

---

## Modos del Receptor (`--receptor`)

### 1. Perfil `human` (Clásico)
Mantiene el comportamiento tradicional de pytest: salida formateada con barras de progreso, colores ANSI y tracebacks de código completos. Es la opción por defecto si no pasas el flag.
```bash
pytest --receptor=human
```

### 2. Perfil `llm` (Optimizado para IA)
Diseñado para consumo por agentes de IA y bucles interactivos de TDD basados en Modelos de Lenguaje.
```bash
pytest --receptor=llm
```
**Características del modo `llm`:**
* **Éxito silencioso:** Genera únicamente un resumen atómico: `OK: N passed in X.XXs`.
* **Marcado XML minificado:** Envuelve los detalles del error en delimitadores semánticos (ej: `<failure_group>`, `<message>`, `<captured_stdout>`) sin sangrías ni saltos de línea estéticos, reduciendo el ruido de atención en el prompt.
* **De-duplicación de errores:** Agrupa fallos idénticos bajo la misma firma del error, listando los tests afectados para ahorrar tokens redundantes.
* **Hints de resolución:** Sugiere comandos de instalación específicos de Poetry, UV, PDM o Pipenv ante excepciones como `ModuleNotFoundError`.

### 3. Perfil `ci` (Integración Continua)
Formato optimizado para terminales de CI/CD no interactivas:
```bash
pytest --receptor=ci
```
**Características del modo `ci`:**
* **Silencioso en éxito:** Si todos los tests pasan, solo muestra una línea final de estado.
* **Latido de Progreso (Heartbeat):** Imprime líneas de progreso planas en intervalos del 10% (ej. `CI Progress: 20% (after 5.0s)`) únicamente si la ejecución tarda más de 5 segundos, evitando *timeouts*.
* **Failures-only:** Si hay fallos, sólo imprime las trazas planas de los tests fallidos (sin colores ANSI).

---

## Características Avanzadas

### Medición de Tokens (`--receptor-stats`)
Calcula en tiempo real los tokens consumidos por el reporte clásico versus el optimizado:
```bash
pytest --receptor=llm --receptor-stats
```
Imprimirá al final:
`<!-- [Receptor Stats] Human: 279 tokens | LLM: 202 tokens | Saved: 27.60% -->`

### Volcado de Registros de Auditoría (`--receptor-dump-dir=ruta`)
Guarda volcados paralelos de ambos reportes en la ruta especificada con nombres de archivo únicos (`pytest_human_YYYYMMDD_HHMMSS_PID.log` y `pytest_llm_YYYYMMDD_HHMMSS_PID.log`):
```bash
pytest --receptor=llm --receptor-dump-dir=./test_logs
```
