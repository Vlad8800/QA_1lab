param([switch]$NoPause)

# ASCII-only source so Windows PowerShell 5.1 parses it in any code page.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-1\Scripts\python.exe'
$oldPython = $env:LAB6_PYTHON
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python not found: $python"
}

Push-Location $projectRoot
try {
    if (-not [string]::IsNullOrWhiteSpace((git status --porcelain | Out-String))) {
        throw 'Working tree is not clean. Save existing changes first.'
    }

    $originalBranch = (git branch --show-current).Trim()
    $demoBranch = 'codex/lab6-hook-demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $demoFile = 'lab6_hook_demo.py'
    $env:LAB6_PYTHON = $python

    git switch -c $demoBranch | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Could not create demo branch.' }

    @(
        'def demo_rate(value):',
        '    if value == 1: return 1',
        '    if value == 2: return 2',
        '    if value == 3: return 3',
        '    if value == 4: return 4',
        '    if value == 5: return 5',
        '    if value == 6: return 6',
        '    if value == 7: return 7',
        '    if value == 8: return 8',
        '    if value == 9: return 9',
        '    if value == 10: return 10',
        '    if value == 11: return 11',
        '    return 0'
    ) | Set-Content -LiteralPath $demoFile -Encoding ascii

    git add -- $demoFile
    Write-Host ''
    Write-Host '=== FAIL: commit attempt with CC=12 ===' -ForegroundColor Yellow
    Write-Host 'git commit -m "feat: add messy code"'
    $ErrorActionPreference = 'Continue'
    $commitOutput = @(git commit -m 'feat: add messy code' 2>&1)
    $failExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    foreach ($line in $commitOutput) { Write-Host ($line.ToString()) }
    Write-Host "Exit code: $failExit"
    Write-Host 'Last commit (the failed commit must be absent):'
    git log --oneline -1 | Out-Host
    if ($failExit -ne 1) { throw "Hook did not block the commit: exit $failExit." }
    if (-not $NoPause) { Read-Host 'Take the FAIL screenshot, then press Enter' | Out-Null }

    @(
        'RATES = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11}',
        '',
        'def demo_rate(value):',
        '    return RATES.get(value, 0)'
    ) | Set-Content -LiteralPath $demoFile -Encoding ascii

    git add -- $demoFile
    Write-Host ''
    Write-Host '=== PASS: lookup-table refactoring ===' -ForegroundColor Green
    Write-Host 'git commit -m "refactor: replace branches with lookup table"'
    $ErrorActionPreference = 'Continue'
    $commitOutput = @(git commit -m 'refactor: replace branches with lookup table' 2>&1)
    $passExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    foreach ($line in $commitOutput) { Write-Host ($line.ToString()) }
    Write-Host "Exit code: $passExit"
    git log --oneline -2 | Out-Host
    if ($passExit -ne 0) { throw "PASS commit failed: exit $passExit." }
    if (-not $NoPause) { Read-Host 'Take the PASS screenshot, then press Enter' | Out-Null }

    git switch $originalBranch | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Could not return to $originalBranch." }
    Write-Host ''
    Write-Host "Done. Current branch: $originalBranch. Demo branch: $demoBranch."
}
finally {
    $env:LAB6_PYTHON = $oldPython
    Pop-Location
}
