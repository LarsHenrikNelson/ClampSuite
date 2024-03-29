# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


project = "ClampSuite"
copyright = "2022, Lars Henrik Nelson"
author = "Lars Henrik Nelson"
release = "0.0.4"

html_logo = "images/logo.png"

html_theme_options = {
    "logo": {
        "text": "ClampSuite documentation",
        "image_light": "images/logo.png",
        "image_dark": "images/logo.png",
    }
}

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_design", "sphinx.ext.intersphinx"]

templates_path = ["_templates"]
exclude_patterns = []

html_logo = "images/logo.png"

html_theme_options = {
    "logo": {
        "text": "ClampSuite documentation",
        "image_light": "images/logo.png",
        "image_dark": "images/logo.png",
    }
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]

html_theme_options = {
    "github_url": "https://github.com/LarsHenrikNelson/ClampSuite",
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "use_edit_page_button": False,
    "secondary_sidebar_items": ["page-toc"],
    "navigation_with_keys": False,
}
