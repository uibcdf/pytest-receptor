# Documentación de `pytest-receptor`

Bienvenido a la documentación oficial de `pytest-receptor`, el plugin de pytest diseñado para la era de la inteligencia artificial y el desarrollo guiado por agentes.

---

## ¿Qué es `pytest-receptor`?

`pytest-receptor` introduce el concepto de **Receptor (Consumer Profile)** en pytest. Permite adaptar por completo las heurísticas del reporte de resultados y trazas de error de las pruebas según *quién* va a digerir la información (un programador humano, un agente autónomo de IA, o un servidor de integración continua).

```{toctree}
---
maxdepth: 2
caption: "Contenidos:"
---
installation
usage
benchmarks
```

---

## Características de un Vistazo

* **`--receptor=human` (Por defecto):** Salida tradicional, bonita y amigable.
* **`--receptor=llm`:** XML minificado optimizado para tokens de contexto de IA con de-duplicación, hints de reparación y stack trace filtrado.
* **`--receptor=ci`:** Formato plano, silencioso en éxito (zero log bloat) y progresivo mediante latidos de progreso en tiempo real.
* **Estadísticas de Performance:** Detección automática y reporte de los tests lentos que superen el umbral de 0.5s en los logs.
