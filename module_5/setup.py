from setuptools import setup, find_packages

setup(
    name="module_5_app",
    version="1.0.0",
    description="Secure Flask application for GradCafe data analysis",
    author="Vishal Srivastava",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "flask",
        "psycopg[binary]",
        "requests",
        "beautifulsoup4",
    ],
    include_package_data=True,
    zip_safe=False,
)
