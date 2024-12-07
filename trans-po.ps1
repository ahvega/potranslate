# Script: trans-po.ps1
# Purpose: Manages the translation process of PO files using a Python script and DeepL API
# Requirements: Python virtual environment with required packages, .env file with DeepL API key

# Define mandatory parameter for the input file
param(
    [Parameter(Mandatory=$true)]
    [string]$filename  # Name of the PO file to translate
)

# Set up virtual environment paths
# Using .venv as the standard virtual environment directory name
$venvPath = Join-Path $PSScriptRoot ".venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

# Verify virtual environment exists
# This environment should contain all required Python packages (polib, deepl, etc.)
if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found. Please set up the virtual environment first."
    exit 1
}

# Activate virtual environment if not already active
# This ensures we use the correct Python environment with all dependencies
if (-not ($env:VIRTUAL_ENV)) {
    Write-Host "Activating virtual environment..."
    try {
        & $venvActivate
    }
    catch {
        Write-Host "Failed to activate virtual environment: $_"
        exit 1
    }
}

# Check existence of input PO file
# Script requires a valid PO file to process
if (-not (Test-Path $filename)) {
    Write-Host "Error: Input file '$filename' not found."
    exit 1
}

# Verify .env file exists
# This file should contain DEEPL_API_KEY=your_api_key
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Error: .env file not found. Please create it with your DeepL API key."
    exit 1
}

# Execute the Python translation script
# The script handles the actual translation using DeepL API
$pythonScript = Join-Path $PSScriptRoot "translate-po.py"
try {
    python $pythonScript $filename
}
catch {
    Write-Host "Error running translation script: $_"
    exit 1
} 