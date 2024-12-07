param(
    [Parameter(Mandatory=$true)]
    [string]$FilePrefix
)

# Remove previous result file
$filesToDelete = Get-ChildItem -Path (Resolve-Path "~\Downloads") -Filter "*-es_ES.po"
foreach ($file in $filesToDelete) {
    Remove-Item $file.FullName
}

# Construct file names
$sourceFile = "$FilePrefix-es.po"
$sourceFullPath = Join-Path (Resolve-Path "~\Downloads") $sourceFile
$resultFile = "$FilePrefix-es_ES.po"

# Check if source file exists in Downloads
if (-not (Test-Path $sourceFullPath)) {
    Write-Error "Error: File '$sourceFile' not found in Downloads folder"
    exit 1
}

# Check if trans-po.ps1 exists in current directory
if (-not (Test-Path ".\trans-po.ps1")) {
    Write-Error "Error: trans-po.ps1 not found in current directory"
    exit 1
}

try {
    # Move file from Downloads to current directory
    Write-Host "Moving $sourceFile from Downloads..."
    Move-Item -Path $sourceFullPath -Destination "." -ErrorAction Stop

    # Run trans-po.ps1
    Write-Host "Processing with trans-po.ps1..."
    & ".\trans-po.ps1" $sourceFile

    # Check if result file was created
    if (-not (Test-Path $resultFile)) {
        throw "Result file '$resultFile' was not created by trans-po.ps1"
    }

    # Move result file back to Downloads
    Write-Host "Moving result file to Downloads..."
    Move-Item -Path $resultFile -Destination (Resolve-Path "~\Downloads") -ErrorAction Stop

    # Delete the original file from current directory
    Write-Host "Cleaning up..."
    Remove-Item -Path $sourceFile -ErrorAction Stop

    Write-Host "Process completed successfully"
}
catch {
    Write-Error "An error occurred: $_"
    exit 1
}
