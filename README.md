# pytest-receptor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Pytest Version](https://img.shields.io/badge/pytest-%3E%3D8.0.0-green)](https://docs.pytest.org/)

`pytest-receptor` es un plugin para Pytest diseñado en la era de la inteligencia artificial. Introduce el concepto de **Receptor (Consumer Profile)** para desacoplar el motor de ejecución de pruebas de la forma cosmética en que se reportan, optimizando la densidad de la información y reduciendo drásticamente el consumo de tokens de contexto para Agentes de IA (como Claude Code, Aider, Codex) y servidores de Integración Continua (CI/CD).

---

## 🚀 Características Principales

* **`--receptor=llm` (Modo Optimizado para IA):**
  * **Silencio en éxito:** Si todos los tests pasan, responde con una única línea de éxito: `OK: 42 passed in 1.23s`.
  * **De-duplicación (Dumping):** Agrupa automáticamente múltiples fallos que tengan la misma excepción y mensaje de error bajo una sola etiqueta `<failure_group>`.
  * **Smart Fingerprinting (Sanitización):** Remueve direcciones de memoria hexadecimales (`0x...`) y marcas de tiempo dinámicas en los errores antes de agruparlos para que fallas idénticas se consoliden perfectamente.
  * **Traceback simplificado:** Omite el código fuente redundante de las trazas (que la IA ya tiene en su contexto indexado) y limpia los frames de dependencias en `site-packages` dejando solo la traza de llamadas local.
  * **Hints adaptativos:** Detecta si tu repositorio usa Poetry, UV, PDM o Pipenv y sugiere el comando exacto para instalar dependencias faltantes (ej: `<hint>poetry add requests</hint>`).
  * **Compresión de Diffs:** Trunca automáticamente los diffs de aserción masivos a un máximo de 1500 caracteres para evitar saturación de la ventana de contexto.

* **`--receptor=ci` (Silent-on-Success para CI/CD):**
  * **Silencio absoluto en verde:** No genera salidas interactivas durante la ejecución. Si pasa la suite, solo imprime `CI: N passed in Xs`.
  * **Failures-Only en rojo:** Imprime únicamente las trazas y diffs de los tests que fallaron en texto plano limpio (sin colores ANSI redundantes).
  * **CI Heartbeat (Anti-Timeout):** En ejecuciones lentas de más de 5 segundos, emite un latido de progreso plano cada 5 segundos para mantener activo el servidor de CI/CD (ej: `CI Progress: 45% (after 5.2s)`).

* **Reporte de Performance (Tests Lentos):**
  * Al finalizar, reporta los top 3 tests más lentos que superen el umbral de **0.5s** en ambos modos (`llm` y `ci`).

* **Herramientas de Auditoría:**
  * **`--receptor-stats`:** Añade un comentario comparando los tokens consumidos por la terminal tradicional vs la optimizada.
  * **`--receptor-dump-dir=ruta`:** Guarda en disco volcados de registros comparativos únicos (`pytest_human_*.log` y `pytest_llm_*.log`) firmados con fecha y PID del proceso.

---

## 📊 Benchmarks de Ahorro de Tokens (tiktoken: cl100k_base)

| Escenario / Casuística | Salida Human (Tokens) | Salida LLM (Tokens) | Ahorro Promedio (%) |
| :--- | :---: | :---: | :---: |
| **Warnings** (Silenciado de deprecaciones) | 198 | 12 | **93.94%** |
| **Green Suite** (Todos pasados) | 99 | 12 | **87.88%** |
| **Cascade Failures** (Fallo de fixture en 20 tests) | 1864 | 303 | **83.74%** |
| **Mixed States** (Skipped, xfail, xpass) | 118 | 26 | **77.97%** |
| **Red Suite** (Fallo de aserción simple) | 312 | 163 | **47.76%** |
| **Multiple Failures** (Setup + Call) | 269 | 185 | **31.23%** |
| **Collection Error** (Error de importación) | 279 | 202 | **27.60%** |

---

## 🛠️ Instalación

Instala `pytest-receptor` utilizando `pip` o tu gestor de paquetes favorito:

```bash
pip install pytest-receptor
```

Para instalarlo en modo desarrollo local clonando el repositorio:

```bash
git clone https://github.com/uibcdf/pytest-receptor.git
cd pytest-receptor
pip install -e .[dev]
```

---

## 📖 Uso

El plugin se activa mediante el argumento `--receptor` en la CLI de pytest:

### 1. Salida Clásica para Humanos (Por defecto)
```bash
pytest --receptor=human
```

### 2. Salida Densificada en XML para Agentes LLM
```bash
pytest --receptor=llm
```

### 3. Salida Limpia y Plana para Integración Continua (GitHub Actions, etc.)
```bash
pytest --receptor=ci
```

### 4. Mostrar estadísticas comparativas de tokens
```bash
pytest --receptor=llm --receptor-stats
```

### 5. Volcar ambos reportes a disco para auditoría
```bash
pytest --receptor=llm --receptor-dump-dir=./test_logs
```

---

## 🛡️ Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](file:///home/diego/repos@uibcdf/pytest-receptor/LICENSE) para obtener más detalles.