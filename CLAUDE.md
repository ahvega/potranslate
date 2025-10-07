# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PO File Translator - A tool for automating the translation of PO (Portable Object) files used in software localization, primarily for WordPress plugins/themes. Supports multiple translation APIs including DeepL, Google Cloud Translate, and DeepSeek.

## Development Environment Setup

**Virtual Environment:**

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Required Environment Variables (.env file):**

- `DEEPL_API_KEY` - DeepL API key (for DeepL translation)
- `DEEPSEEK_API_KEY` - DeepSeek API key (for DeepSeek translation)
- `GOOGLE_CLOUD_PROJECT` - Google Cloud project ID (for Google translation)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud service account JSON (for Google translation)

## Common Commands

**Translation Workflows:**

```powershell
# Translate a PO file directly
.\trans-po.ps1 -filename "path\to\file.po"

# Process file from Downloads folder
.\process-po.ps1 -FilePrefix "plugin-name-1142"
# Expects: plugin-name-1142-es.po in Downloads
# Outputs: plugin-name-1142-es_ES.po back to Downloads

# Multi-API translation
python translate-po-multiple.py input.po output.po --api deepl --target-lang es
python translate-po-multiple.py input.po output.po --api google --target-lang es
python translate-po-multiple.py input.po output.po --api deepseek --target-lang es
```

**WordPress Translation Workflow (WP-CLI):**

```powershell
# 1. Generate POT and PO files from source
.\make-po.ps1 es  # Creates languages/foldername-es_ES.po

# 2. Translate the PO file (manual or automated)
.\trans-po.ps1 -filename "languages\foldername-es_ES.po"

# 3. Compile PO to MO
.\make-mo.ps1 es  # Creates languages/foldername-es_ES.mo
```

## Architecture

### Core Translation Scripts

**translate-po.py** - Simple single-API translator

- Uses DeepL API exclusively
- Command line args: `input_file`, `--target-lang` (default: ES)
- Output format: `{basename}_{target_lang}.po`
- Preserves HTML formatting via DeepL's `preserve_formatting=True`

**translate-po-multiple.py** - Multi-API translator with advanced features

- Supports: DeepL, DeepSeek (OpenAI-compatible), Google Cloud Translate
- HTML/variable preservation via regex isolation and reinsertion
- Retry logic with exponential backoff (max 3 retries)
- Rate limiting with configurable delays (default 0.5s between entries)
- Language code mapping for API compatibility

### PowerShell Automation Scripts

**trans-po.ps1** - Virtual environment wrapper

- Activates `.venv` if not already active
- Validates input file and `.env` existence
- Executes `translate-po.py`

**process-po.ps1** - Downloads folder workflow

- Cleans previous `-es_ES.po` files from Downloads
- Moves source file from Downloads → project directory
- Calls `trans-po.ps1` for translation
- Moves result back to Downloads
- Cleans up temporary files

**make-po.ps1** - WordPress POT/PO generation (WP-CLI)

- Creates `languages/` directory if missing
- Generates POT: `wp i18n make-pot . languages/{foldername}.pot`
- Creates/updates PO: `wp i18n make-po` or `wp i18n update-po`
- Naming: `{foldername}-{language}_{LANGUAGE}.po` (e.g., `plugin-es_ES.po`)

**make-mo.ps1** - WordPress MO compilation (WP-CLI)

- Compiles PO to MO: `wp i18n make-mo`
- Validates PO file existence before compilation

### Translation API Integration

**DeepL** (translate-po.py)

- Uses `deepl` Python library
- Built-in HTML preservation

**DeepSeek** (translate-po-multiple.py)

- OpenAI-compatible API via `openai` library
- Base URL: `https://api.deepseek.com`
- Model: `deepseek-chat`
- Temperature: 1.3 (recommended for translations)
- System prompt enforces HTML/variable preservation

**Google Cloud Translate** (translate-po-multiple.py)

- Uses `google.cloud.translate_v3` library
- Requires service account authentication via JSON key
- Language code mapping: `es_ES` → `es`, `en_US` → `en`, etc.
- MIME type: `text/plain` (HTML handled separately)

### HTML and Variable Preservation

**Isolation Strategy** (translate-po-multiple.py):

1. `isolate_html_and_variables()` - Extracts HTML tags and variables (`%s`, `%d`, `{0}`)
2. Replaces with placeholders: `{{HTML}}`, `{{VAR}}`
3. Translates cleaned text
4. `reinsert_html_and_variables()` - Restores original tags/variables in order

This ensures technical elements survive translation unmodified.

## Code Style (from CRUSH.md)

**Python:**

- Use `snake_case` for variables and functions
- Include type hints for function signatures
- Use `flake8`/`black` for formatting
- Use `isort` for import organization

**PowerShell:**

- Use `PascalCase` for functions and variables
- Use `PSScriptAnalyzer` for analysis

**General:**

- Store API keys in `.env` file, load with `python-dotenv`
- Implement comprehensive error handling for API calls and file I/O
- Always use `.venv` virtual environment

## File Naming Conventions

**Input/Output Patterns:**

- WordPress source: `{plugin/theme-name}-{lang}.po` → Translation → `{plugin/theme-name}-{lang}_{LANG}.po`
- Example: `elementor-es.po` → `elementor-es_ES.po`
- WordPress POT: `{foldername}.pot`
- WordPress PO/MO: `{foldername}-{lang}_{LANG}.po/.mo`

## Dependencies

Core dependencies (requirements.txt):

- `polib>=1.2.0` - PO file parsing
- `deepl>=1.16.1` - DeepL API client
- `tqdm>=4.66.1` - Progress bars
- `python-dotenv>=1.0.0` - Environment variables

Additional dependencies (translate-po-multiple.py):

- `requests` - HTTP for DeepSeek API
- `openai` - DeepSeek API client
- `google-cloud-translate` - Google Cloud Translate v3

## Important Notes

- The `.gitignore` excludes `*.po` files except for preserved test files - be careful not to commit sensitive translation data
- The Google Cloud service account JSON (`translator-450208-74f3fffcc975.json`) is also gitignored
- WP-CLI workflows assume script is run from plugin/theme root directory
- File naming must match WordPress locale format: `{textdomain}-{locale}.mo` (e.g., `myplugin-es_ES.mo`)
