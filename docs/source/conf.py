# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os

project = "ClampSuite"
copyright = "2022, Lars Henrik Nelson"
author = "Lars Henrik Nelson"
release = "0.0.4"

html_logo = "images/logo.png"

json_url = "https://clampsuite.readthedocs.io/en/latest/_static/switcher.json"
version_match = os.environ.get("READTHEDOCS_VERSION")
release = "0.0.5"
# If READTHEDOCS_VERSION doesn't exist, we're not on RTD
# If it is an integer, we're in a PR build and the version isn't correct.
# If it's "latest" → change to "dev" (that's what we want the switcher to call it)
if not version_match or version_match.isdigit() or version_match == "latest":
    # For local development, infer the version to match from the package.
    if "dev" in release or "rc" in release:
        version_match = "dev"
        # We want to keep the relative reference if we are in dev mode
        # but we want the whole url if we are effectively in a released version
        json_url = "_static/switcher.json"
    else:
        version_match = f"v{release}"
elif version_match == "stable":
    version_match = f"v{release}"

html_theme_options = {
    "logo": {
        "text": "ClampSuite documentation",
        "image_light": "images/logo.png",
        "image_dark": "images/logo.png",
    },
    "show_nav_level": 3,
    "switcher": {
        "json_url": json_url,
        "version_match": version_match,
    },
    "navbar_center": ["version-switcher", "navbar-nav"],
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
