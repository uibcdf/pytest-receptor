import os
import sys
sys.path.insert(0, os.path.abspath("../src"))

project = "pytest-receptor"
copyright = "2026, uibcdf"
author = "uibcdf"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}
# Generate anchors for headings down to h3, so pages can link to each other's
# sections instead of only to whole pages.
myst_heading_anchors = 3

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
]
