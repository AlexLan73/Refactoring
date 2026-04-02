"""Sphinx config for discriminator_estimates (FFT frequency discriminators)."""
import os
import sys
# Относительный путь к tsignal пакету (стенд TSignalFrequency)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(_here,
                    "..", "..", "..", "..", "..", "Python", "TSignalFrequency")))

project = "Discriminator Estimates — FFT Frequency"
author = "Федоров С.А., Добродумов А.Б., Alex + Kodo (AI)"
release = "1.0"
language = "ru"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]

autodoc_member_order = "bysource"
napoleon_google_docstring = True

html_theme = "sphinx_rtd_theme"
html_static_path = []
html_title = "Discriminator Estimates — FFT Frequency Discriminators"
