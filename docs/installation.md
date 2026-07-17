# Instalación

Esta página detalla cómo instalar y configurar `pytest-receptor` en diferentes entornos.

---

## Requisitos Previos

`pytest-receptor` requiere:
* **Python:** Versión `>= 3.8` (incluyendo soporte completo para Python `3.13`).
* **Pytest:** Versión `>= 8.0.0`.

---

## Instalación Estable (PyPI)

Para instalar la versión estable más reciente directamente desde el repositorio oficial de paquetes de Python (PyPI):

```bash
pip install pytest-receptor
```

O agrégalo a las dependencias de tu proyecto según el gestor que utilices:

* **Poetry:**
  ```bash
  poetry add --group dev pytest-receptor
  ```
* **Pipenv:**
  ```bash
  pipenv install --dev pytest-receptor
  ```
* **PDM:**
  ```bash
  pdm add -d pytest-receptor
  ```
* **UV:**
  ```bash
  uv pip install pytest-receptor
  ```

---

## Instalación desde Código Fuente (Desarrollo)

Si deseas clonar el repositorio para desarrollo local o probar cambios:

1. Clona el repositorio desde GitHub:
   ```bash
   git clone https://github.com/uibcdf/pytest-receptor.git
   cd pytest-receptor
   ```

2. Instala en modo editable junto con las dependencias de desarrollo (`dev`):
   ```bash
   pip install -e .[dev]
   ```
