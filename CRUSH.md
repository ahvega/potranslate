# Potranslate CRUSH.md

This document outlines the development conventions for the Potranslate project.

## Commands

- **Activate Environment**: `.\.venv\Scripts\Activate.ps1`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run a translation**: `.\trans-po.ps1 -filename "path\to\your\file.po"`
- **Process a file from Downloads**: `.\process-po.ps1 -FilePrefix "your-file-prefix"`

## Code Style

### Python

- **Formatting**: Use a linter like `flake8` or a formatter like `black` for consistent code formatting.
- **Imports**: Use `isort` to sort and organize imports.
- **Naming**: Use `snake_case` for variables and functions.
- **Types**: Use type hints for function signatures.

### PowerShell

- **Formatting**: Use the `PSScriptAnalyzer` for code analysis and formatting.
- **Naming**: Use `PascalCase` for functions and variables.

### General

- **Secrets**: Store secrets like API keys in a `.env` file and use `python-dotenv` to load them.
- **Error Handling**: Implement comprehensive error handling, especially for API calls and file I/O operations.
- **Dependencies**: Keep the `requirements.txt` file up-to-date with all necessary packages.
- **Virtual Environment**: Always use the designated virtual environment to maintain dependency isolation.
