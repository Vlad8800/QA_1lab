param([switch]$NoPause)

# ASCII-only source for Windows PowerShell 5.1 compatibility.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-1\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python not found: $python"
}

$demoDir = Join-Path $env:TEMP ('lab6-radon-history-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $demoDir | Out-Null

Push-Location $projectRoot
try {
    foreach ($stage in @(
        @{ Name = 'BASELINE'; Ref = 'c44aa3a'; Expected = 10 },
        @{ Name = 'FAIL'; Ref = '5e21045'; Expected = 16 }
    )) {
        $sourcePath = Join-Path $demoDir ($stage.Name.ToLower() + '-services.py')
        $gitSpec = $stage.Ref + ':app/services.py'
        & $python -c "import subprocess,sys;open(sys.argv[2],'wb').write(subprocess.check_output(['git','show',sys.argv[1]]))" $gitSpec $sourcePath
        if ($LASTEXITCODE -ne 0) { throw "Could not read $gitSpec" }

        Write-Host ''
        Write-Host ('=== ' + $stage.Name + ' - Radon CLI ===') -ForegroundColor Yellow
        Write-Host ('Source revision: ' + $stage.Ref + ' (app/services.py)')
        Write-Host ('Command: python -m radon cc ' + $sourcePath + ' -s -n B')
        $scan = & $python -m radon cc $sourcePath -s -n B
        if ($LASTEXITCODE -ne 0) { throw "Radon failed for $gitSpec" }
        $scan | Out-Host

        $target = $scan | Select-String 'calculate_shipping_cost - [A-F] \(([0-9]+)\)'
        if (-not $target) { throw 'Target function missing from Radon output.' }
        $actual = [int]$target.Matches[0].Groups[1].Value
        if ($actual -ne $stage.Expected) {
            throw "Expected CC=$($stage.Expected); Radon measured CC=$actual."
        }
        Write-Host ("Verified calculate_shipping_cost: CC=$actual") -ForegroundColor Green
        if (-not $NoPause) {
            Read-Host ('Take the ' + $stage.Name + ' screenshot, then press Enter') | Out-Null
        }
    }
    Write-Host ''
    Write-Host 'Done. Git branch and working tree were not changed.'
}
finally {
    Pop-Location
}
