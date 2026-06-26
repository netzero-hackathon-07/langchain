$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$backendDir = Join-Path $repoRoot "backend"
$outDir = Join-Path $backendDir "dist"
$zipPath = Join-Path $outDir "ecoroute_lambda.zip"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive `
    -Path (Join-Path $backendDir "lambda_function.py") `
    -DestinationPath $zipPath `
    -Force

Write-Host "Created: $zipPath"
