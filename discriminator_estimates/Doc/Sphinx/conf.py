"""Sphinx config for discriminator_estimates module (furo theme)."""
from datetime import datetime

# --- Project information ---
project = "Discriminator Estimates"
author = "Кодо (AI) + Alex"
release = "2.0"
language = "ru"
copyright = f"{datetime.now().year}, {author}"

# --- General configuration ---
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinx_copybutton",
]

# MyST extensions — рич-расширения Markdown
myst_enable_extensions = [
    "amsmath",
    "dollarmath",
    "colon_fence",
    "deflist",
    "tasklist",
    "fieldlist",
]

# --- HTML output / Furo ---
html_theme = "furo"
html_title = "Discriminator Estimates"
html_short_title = "DiscrEst"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view"],
    # Цвета: тёмно-синий как в нашем отчёте
    "light_css_variables": {
        "color-brand-primary":  "#1f4e79",
        "color-brand-content":  "#1f4e79",
        "color-admonition-background": "#f0f9ff",
    },
    "dark_css_variables": {
        "color-brand-primary":  "#60a5fa",
        "color-brand-content":  "#93c5fd",
    },
}

html_css_files = ["custom.css"]

# Нумерация рисунков и формул
numfig = True
math_numfig = True
math_eqref_format = "({number})"

# Подсветка кода — по умолчанию C
highlight_language = "c"

# Copy-button: подсвечиваем только prompt
copybutton_prompt_text = r">>> |\$ "
copybutton_prompt_is_regexp = True

# Source suffixes
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Master document
master_doc = "index"

# Не падать при первом warning — быстрее итерации
keep_going = True

# Napoleon (для автодока, если появятся Python-биндинги)
autodoc_member_order = "bysource"
napoleon_google_docstring = True
