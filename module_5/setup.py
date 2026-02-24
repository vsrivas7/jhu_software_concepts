"""
setup.py — makes module_5 an installable Python package.

Why this matters:
  - `pip install -e .` makes src/ importable from anywhere without sys.path hacks.
  - Ensures consistent imports in local development, CI, and production.
  - uv can read install_requires to sync environments automatically.
  - Eliminates "works on my machine" import errors across different environments.
"""

from setuptools import find_packages, setup

setup(
    name="gradcafe-app",
    version="0.1.0",
    description="GradCafe scraper and Flask web application",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "Flask",
        "psycopg[binary]",
        "requests",
        "beautifulsoup4",
        "python-dotenv",
        "lxml",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "pylint",
            "pydeps",
        ]
    },
)
