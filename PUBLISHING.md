# Publishing Python-Import-Analyzer to PyPI

This document provides detailed instructions on how to publish this package to the Python Package Index (PyPI).

## Prerequisites

1. Create accounts on both [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/).
2. Install required publishing tools:
   ```bash
   pip install build twine
   ```

## Preparing for Release

1. **Update Version Number**:
   - In `setup.py`:
     ```python
     setup(
         name="python-import-analyzer",
         version="x.y.z",  # Update this version number
         ...
     )
     ```
   - In `python_import_analyzer/__init__.py`:
     ```python
     __version__ = "x.y.z"  # Update this version number
     ```
   
   Follow [semantic versioning](https://semver.org/) guidelines:
   - MAJOR version for incompatible API changes
   - MINOR version for adding functionality in a backward compatible manner
   - PATCH version for backward compatible bug fixes

2. **Update CHANGELOG.md** (if you have one):
   - Add a new entry for the version you're about to release
   - Include all notable changes, additions, and fixes

3. **Ensure all tests pass**:
   ```bash
   pytest
   ```

## Building Distribution Packages

1. Clean previous builds:
   ```bash
   rm -rf build/ dist/ *.egg-info/
   ```

2. Build both source and wheel distributions:
   ```bash
   python -m build
   ```
   
   This will create two files in the `dist/` directory:
   - `python_import_analyzer-x.y.z.tar.gz` (source archive)
   - `python_import_analyzer-x.y.z-py3-none-any.whl` (wheel)

## Testing on TestPyPI

It's a good practice to first upload to TestPyPI to verify the package works correctly.

1. Upload to TestPyPI:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. Install from TestPyPI in a new virtual environment:
   ```bash
   python -m venv test_env
   source test_env/bin/activate  # On Windows: test_env\Scripts\activate
   pip install --index-url https://test.pypi.org/simple/ --no-deps python-import-analyzer
   ```

3. Verify the package works:
   ```bash
   import-analyzer  # This should start the dashboard
   ```

## Publishing to PyPI

Once you've verified the package works correctly on TestPyPI, you can publish it to the real PyPI:

1. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```

2. Enter your PyPI username and password when prompted.

## After Publishing

1. Create a Git tag for the release:
   ```bash
   git tag -a vx.y.z -m "Release version x.y.z"
   git push --tags
   ```

2. Update GitHub release notes (if you use GitHub).

## Troubleshooting

- If you get an error about long descriptions, make sure your README.md is properly formatted.
- If you encounter upload errors, check your PyPI/TestPyPI credentials.
- To avoid duplicate uploads, use `twine check dist/*` before uploading.

## Automation with GitHub Actions

Consider automating the release process with GitHub Actions:

1. Create `.github/workflows/publish.yml`:
   ```yaml
   name: Publish to PyPI

   on:
     release:
       types: [created]

   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.x'
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install build twine
       - name: Build and publish
         env:
           TWINE_USERNAME: ${{ secrets.PYPI_USERNAME }}
           TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
         run: |
           python -m build
           twine upload dist/*
   ```

2. Add your PyPI username and password as GitHub repository secrets.

With this setup, a new PyPI release will be triggered automatically when you create a new release on GitHub.
