# Testing Python-Import-Analyzer

This document outlines how to run tests for the Python-Import-Analyzer package.

## Setting Up Test Environment

1. Install testing dependencies:
   ```bash
   pip install pytest pytest-mock pytest-cov
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Running Tests

### Basic Test Execution

Run all tests:
```bash
pytest
```

### Test with Coverage Report

Run tests and generate a coverage report:
```bash
pytest --cov=python_import_analyzer
```

For a detailed HTML coverage report:
```bash
pytest --cov=python_import_analyzer --cov-report=html
```
Then open `htmlcov/index.html` in your browser.

### Running Specific Tests

Run tests in a specific file:
```bash
pytest tests/test_dependency_analyzer.py
```

Run a specific test:
```bash
pytest tests/test_dependency_analyzer.py::test_find_python_files
```

### Test Options

- `-v`: Verbose output
- `--cov`: Generate coverage report
- `-xvs`: Exit on first failure, verbose output, no output capture

Example:
```bash
pytest -xvs tests/
```

## Continuous Integration

This project uses GitHub Actions for continuous integration. Tests are run automatically on every push and pull request.

## Writing Tests

When writing new tests:

1. Place them in the `tests/` directory
2. Name test files with prefix `test_`
3. Name test functions with prefix `test_`
4. Use meaningful names that describe what is being tested
5. Follow the Arrange-Act-Assert pattern

Example:
```python
def test_find_python_files():
    # Arrange
    test_dir = "test_directory"
    os.makedirs(test_dir, exist_ok=True)
    with open(f"{test_dir}/test_file.py", "w") as f:
        f.write("print('Hello, World!')")
    
    # Act
    result = find_python_files(test_dir)
    
    # Assert
    assert len(result) == 1
    assert result[0].endswith("test_file.py")
    
    # Cleanup
    shutil.rmtree(test_dir)
```

## Mock Data

For testing, we provide sample Python projects in `tests/test_data/`. You can use these for integration tests.
