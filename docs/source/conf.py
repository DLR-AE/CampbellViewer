# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CampbellViewer"
copyright = "2022, J. Rieke, H. Verdonck, O. Hach, N. Joeres"
author = "J. Rieke, H. Verdonck, O. Hach, N. Joeres"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
# html_theme_options = {"logo_only": True}
html_theme_options = {
        "show_prev_next": False,
        "navigation_with_keys": False
    }

html_logo = "./images/sample_icon.png"

html_static_path = ["_static"]
# html_css_files = ["css/custom.css"]


# -- Extension configuration -------------------------------------------------
autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order="groupwise" # sorting of functions etc.
autodoc_default_options = {
    "members": True, #
    "member-order": "bysource", # "groupwise", "alphabetical"
    "undoc-members": True,
}
