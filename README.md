# PO File Translator

A tool for automating the translation of PO (Portable Object) files using DeepL API.

## Author

Adalberto H. Vega

## Description

This project provides a set of scripts to automate the translation of PO files commonly used in software localization. It uses the DeepL API for high-quality translations and maintains the formatting of the original text, including HTML tags.

## Features

- Automated translation of untranslated entries in PO files
- Preserves HTML formatting and tags
- Progress bar showing translation status
- Error handling for failed translations
- Support for different target languages (default: Spanish)
- Virtual environment management

## Requirements

- Python 3.x
- PowerShell
- DeepL API key
- Virtual environment (.venv)

### Python Dependencies

- polib: For handling PO files
- deepl: DeepL API client
- python-dotenv: For environment variable management
- tqdm: For progress bar functionality

## Setup

1. Clone the repository
2. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with your DeepL API key:

   ```env
   DEEPL_API_KEY=your-api-key-here
   ```

## Usage

### Basic Translation

To translate a PO file:

```powershell
.\trans-po.ps1 -filename "path\to\your\file.po"
```

### Processing Files from Downloads

To process a PO file from your Downloads folder:

```powershell
.\process-po.ps1 -FilePrefix "your-file-prefix"
```

For example, if your file is named "elementor-1142-es.po", use:

```powershell
.\process-po.ps1 -FilePrefix "elementor-1142"
```

The script will:

1. Look for the file in your Downloads folder
2. Process the translation
3. Save the result as "elementor-1142-es_ES.po" back in your Downloads folder

### Output Files

- Input file format: `filename-es.po`
- Output file format: `filename-es_ES.po`

### Common Issues

- Make sure your `.env` file contains a valid DeepL API key
- Virtual environment must be set up before running the scripts
- Input files must be valid PO format files

## License

MIT License

Copyright (c) 2024 Adalberto H. Vega
