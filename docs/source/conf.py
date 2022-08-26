# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'CampbellViewer'
copyright = '2022, J. Rieke, H. Verdonck, O. Hach, N. Joeres'
author = 'J. Rieke, H. Verdonck, O. Hach, N. Joeres'
release = 'DEVEL'



# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {"logo_only": True, "navigation_with_keys": True}

html_static_path = ['_static']
html_css_files = ["css/custom.css"]
