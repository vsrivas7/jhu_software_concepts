import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

project = 'Grad Cafe Analytics'
copyright = '2025, Vishal Srivastava'
author = 'Vishal Srivastava'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_mock_imports = [
    'flask',
    'psycopg',
    'requests',
    'bs4',
]