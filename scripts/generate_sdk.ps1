param([string]$OutputDirectory = 'sdk-client')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
try {
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        throw 'Install Java 17+ and add java to PATH; the SDK is generated locally.'
    }
    python -m pip install openapi-generator-cli
    if ($LASTEXITCODE -ne 0) { throw 'OpenAPI Generator installation failed' }
    openapi-generator-cli generate -i docs/api/openapi.yaml -g python -o $OutputDirectory --additional-properties=packageName=qa1lab_client,packageVersion=1.0.0
    if ($LASTEXITCODE -ne 0) { throw 'SDK generation failed' }
}
finally { Pop-Location }
