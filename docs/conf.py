"""Sphinx configuration for factominer."""

from __future__ import annotations

project = "factominer"
author = "Aigora"
copyright = "2026, Aigora"
release = "0.1.0.dev0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

master_doc = "index"
exclude_patterns = ["_build", "elves", "plans"]

html_theme = "alabaster"
html_title = "factominer"
html_static_path = []

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

myst_enable_extensions = ["colon_fence", "deflist"]
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": False,
}
