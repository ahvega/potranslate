# Script: make-mo.ps1
# Description: PowerShell script to generate WordPress MO files from translated PO files
#
# This script creates the compiled MO file from an existing PO file.
# Make sure you have already:
# 1. Run make-po.ps1 to generate the PO file
# 2. Translated all strings in the PO file
# 3. Saved the translations
#
# Requirements:
# - WP-CLI installed and in PATH
# - Translated PO file in languages directory
#
# Usage:
# 1. Place this script in your plugin/theme root directory
# 2. Run: .\make-mo.ps1 [language]
#    - language: Optional 2-letter language code (e.g. es, fr, de)
#    - If not provided, script will prompt for language code
#    - Defaults to 'es' if no input given
#
param([string]$language = "")

if ([string]::IsNullOrEmpty($language)) {
    $language = Read-Host "Enter language code (e.g. es, fr, de) [default: es]"
    if ([string]::IsNullOrEmpty($language)) {
        $language = "es"
    }
}

# Convert language code to uppercase country code format (e.g. es -> es_ES)
$language = $language.ToLower()
$LANG = $language.ToUpper()
$langCode = "${language}_${LANG}"

Write-Host "Using language code: $langCode"

# Get the current folder name
$folderName = Split-Path -Path (Get-Location) -Leaf

# Check if wp-cli is available
if (!(Get-Command wp -ErrorAction SilentlyContinue)) {
    Write-Error "WP-CLI not found in PATH. Please install it and try again."
    exit 1
}

# Check if the po file exists
if (!(Test-Path "languages/$folderName-$langCode.po")) {
    Write-Error "PO file not found. Please run make-po.ps1 first and translate the strings."
    exit 1
}

# Make the mo file from the po file
$makeMoCommand = "wp i18n make-mo languages/$folderName-$langCode.po languages/$folderName-$langCode.mo"
Write-Host "Executing: $makeMoCommand"
try {
    Invoke-Expression $makeMoCommand
    Write-Host "`n✅ MO file created successfully!"
    Write-Host "`n📝 The translation files are ready to use!"
} catch {
    Write-Error "Failed to create MO file: $_"
    exit 1
}

