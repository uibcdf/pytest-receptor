Aquí tienes un texto perfectamente estructurado para la sección de la **Guía de Desarrollo** o el **README** de tu repositorio. Está redactado con un tono técnico, claro y motivador, ideal para orientar el rumbo del proyecto desde el primer día:

---

# Guía de Desarrollo: `pytest-receptor`

## 1. El Porqué (La Visión)

El ecosistema del desarrollo de software está experimentando un cambio de paradigma. Cada vez es más común que `pytest` no sea ejecutado por un humano en su terminal, sino por **Agentes de IA y CLIs LLM-nativas** (como Claude Code, Codex CLI, Aider, o bucles autónomos de TDD).

### El problema actual

`pytest` fue diseñado en su núcleo para ojos humanos. Su salida estándar (`stdout`) incluye barras de progreso, decoraciones visuales (`====`), colores ANSI y bloques redundantes de código fuente en los *tracebacks*.

* Para un humano, esto es ergonomía visual.
* Para un Modelo de Lenguaje (LLM), esto es **ruido semántico y un desperdicio masivo de tokens** de contexto, lo que eleva el costo y la latencia del bucle de desarrollo.

Por otro lado, los "trucos" actuales como `--tb=line -q` recortan el texto pero **ciegan al agente**, ya que eliminan los detalles estructurales críticos (como los *diffs* complejos de diccionarios u objetos que fallaron en un `assert`), haciendo que la IA alucine correcciones en bucle.

---

## 2. El Qué (El Objetivo)

El objetivo de `pytest-receptor` es introducir el concepto de **Receptor (Consumer Profile)** en el ecosistema de pruebas de Python. Queremos desacoplar la lógica interna de la ejecución de los tests de la forma cosmética en que se reportan, optimizando la salida según *quién* va a digerir la información.

El plugin expondrá un nuevo flag en la CLI:

```bash
pytest --receptor=[human|llm|ci]

```

* **`--receptor=human` (Por defecto):** Mantiene el comportamiento clásico, visual y amigable de `pytest`.
* **`--receptor=llm` (Nuestra prioridad):** Una salida diseñada puramente para arquitecturas de Transformers. Busca la máxima **densidad de información semántica** al menor costo de tokens posible.
* **`--receptor=ci` (A futuro):** Salida limpia y plana optimizada para motores de logs tradicionales (Jenkins, GitHub Actions) sin animaciones interactivas.

---

## 3. El Cómo (Primeras Ideas de Implementación)

Para construir la variante `--receptor=llm` de forma sólida y eficiente, nos basaremos en los siguientes pilares técnicos:

### A. Heurísticas de Salida Eficientes

* **Silencio en el Éxito (Green Suite):** Si todos los tests pasan, no se listan archivos ni entornos. El plugin responderá con un string atómico y único: `OK: 42 passed in 1.4s`. Cero tokens desperdiciados en regresiones exitosas.
* **Mutilación de Código Redundante:** En caso de fallo, **no** imprimiremos las líneas de código fuente circundantes de la excepción. El agente de IA ya tiene los archivos fuente indexados en su contexto de trabajo; imprimir el código de vuelta en el *stdout* es redundancia pura.

### B. Densidad Semántica mediante XML/Markdown Minificado

En lugar de formatear tablas o líneas de guiones (`----`), envolveremos los fallos en etiquetas estructurales ligeras (ej. `<test_failure>`, `<diff>`). Los modelos de lenguaje modernos han sido entrenados masivamente con datos de la web (HTML/XML); sus mecanismos de atención identifican y procesan los límites de estas etiquetas con un ruido de contexto drásticamente menor que el texto plano arbitrario.

### C. Estrategia de Inyección vía Hooks

No limpiaremos el texto mediante post-procesamiento de strings (lo cual desperdicia ciclos de CPU). En su lugar, interceptaremos el ciclo de vida de `pytest` usando sus hooks nativos:

1. Usar `pytest_addoption` para registrar el flag.
2. Interceptar el `TerminalReporter` en `pytest_configure`.
3. Sobrescribir o cortocircuitar `pytest_runtest_logreport` cuando `--receptor=llm` esté activo, extrayendo directamente los atributos crudos de `ExceptionInfo` (`err.type`, `err.value`, y la localización exacta del frame) para serializarlos directamente en nuestro formato optimizado para tokens.

---

Este texto establece las reglas del juego claras: define el problema económico y técnico de los tokens, plantea la solución como una arquitectura de perfiles y traza la ruta técnica usando los ganchos internos de `pytest`.
