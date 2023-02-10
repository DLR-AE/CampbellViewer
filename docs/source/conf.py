# Configuration file for the Sphinx documentation builder.

import campbellviewer

# -- Project information -----------------------------------------------------

project = "CampbellViewer"
copyright = "2023, J. Rieke, H. Verdonck, O. Hach, N. Joeres"
author = "J. Rieke, H. Verdonck, O. Hach, N. Joeres"

# -- General configuration ---------------------------------------------------

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
# Define the json_url for version switcher.
json_url = "https://raw.githubusercontent.com/DLR-AE/CampbellViewer/gh-pages/switcher.json"

# Define the version we use for matching in the version switcher.
# For local development, infer the version to match from the package.
release = campbellviewer.__version__
if "dev" in release:
    version_match = release
    json_url = "_static/switcher.json"
else:
    version_match = release

html_theme = "pydata_sphinx_theme"
html_theme_options = {
        "show_prev_next": False,
        "navigation_with_keys": False,
        "logo": {
            "text": "CampbellViewer",
            "alt_text": "CampbellViewer",
        },
        "navbar_align": "content",
        "navbar_center": ["navbar-nav"],
        "navbar_end": ["theme-switcher", "version-switcher"],
        "switcher": {
            "json_url": json_url,
            "version_match": version_match,
        },
    }

html_logo = "_static/images/windturbine.png"

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
