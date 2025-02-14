# Script: make-po.ps1
# Description: PowerShell script to generate and update WordPress PO translation files
#
# This script creates/updates PO files for translation:
# 1. Creates a POT template file from the current plugin/theme
# 2. Creates or updates a PO translation file for the specified language
#
# Requirements:
# - WP-CLI installed and in PATH
# - WordPress plugin/theme in current directory
#
# Usage:
# 1. Place this script in your plugin/theme root directory
# 2. Run: .\make-po.ps1 [language]
#    - language: Optional 2-letter language code (e.g. es, fr, de)
#    - If not provided, script will prompt for language code
#    - Defaults to 'es' if no input given
#
# After running this script:
# 1. Open the generated .po file in Poedit or similar editor
# 2. Translate all strings
# 3. Save the translations
# 4. Run make-mo.ps1 to generate the final .mo file
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

# Create languages directory if it doesn't exist
if (!(Test-Path "languages")) {
    New-Item -ItemType Directory -Path "languages"
    Write-Host "Created languages directory"
}

# Build the command using the folder name as the domain and pot filename
$potCommand = "wp i18n make-pot . languages/$folderName.pot --domain=$folderName"
Write-Host "Executing: $potCommand"
try {
    Invoke-Expression $potCommand
} catch {
    Write-Error "Failed to create POT file: $_"
    exit 1
}

# Check if the po file exists
if (Test-Path "languages/$folderName-$langCode.po") {
    # Update existing po file with the new pot file
    $updateCommand = "wp i18n update-po languages/$folderName.pot languages/$folderName-$langCode.po"
    Write-Host "Executing: $updateCommand"
    try {
        Invoke-Expression $updateCommand
        Write-Host "`n✅ PO file updated successfully!"
    } catch {
        Write-Error "Failed to update PO file: $_"
        exit 1
    }
} else {
    # Create new po file from pot file using wp i18n make-po
    $createCommand = "wp i18n make-po languages/$folderName.pot languages/$folderName-$langCode.po"
    Write-Host "Executing: $createCommand" 
    try {
        Invoke-Expression $createCommand
        Write-Host "`n✅ PO file created successfully!"
    } catch {
        Write-Error "Failed to create PO file: $_"
        exit 1
    }
}

Write-Host "`n📝 Next steps:"
Write-Host "1. Open the generated .po file in Poedit or similar editor"
Write-Host "2. Translate all strings"
Write-Host "3. Save the translations"
Write-Host "4. Run make-mo.ps1 to generate the final .mo file"