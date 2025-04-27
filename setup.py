from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python-import-analyzer",
    version="0.1.0",
    author="Weavery",
    author_email="your.email@example.com",
    description="A tool for visualizing and analyzing import dependencies in Python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Python-Import-Analyzer",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/Python-Import-Analyzer/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "networkx",
        "matplotlib",
        "plotly",
        "dash>=2.0.0",
        "dash-cytoscape",
        "pandas",
    ],
    entry_points={
        "console_scripts": [
            "import-analyzer=python_import_analyzer.dependency_dashboard:main",
        ],
    },
)
