param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-1\Scripts\python.exe'
$oldPython = $env:LAB6_PYTHON
if (-not (Test-Path -LiteralPath $python)) {
    throw "Не знайдено Python: $python"
}

Push-Location $projectRoot
try {
    if (-not [string]::IsNullOrWhiteSpace((git status --porcelain | Out-String))) {
        throw 'Робоча папка має незбережені зміни. Спершу заверши або збережи їх.'
    }

    $originalBranch = (git branch --show-current).Trim()
    $demoBranch = 'codex/lab6-hook-demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $demoFile = 'lab6_hook_demo.py'
    $env:LAB6_PYTHON = $python

    git switch -c $demoBranch | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Не вдалося створити демонстраційну гілку.' }

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
    ) | Set-Content -LiteralPath $demoFile -Encoding utf8

    git add -- $demoFile
    Write-Host ''
    Write-Host '=== FAIL: спроба коміту функції з CC=12 ===' -ForegroundColor Yellow
    Write-Host 'git commit -m "feat: add messy code"'
    git commit -m 'feat: add messy code' 2>&1 | Out-Host
    $failExit = $LASTEXITCODE
    Write-Host "Код завершення: $failExit"
    Write-Host 'Останній коміт (невдалий коміт тут зʼявитися не повинен):'
    git log --oneline -1 | Out-Host
    if ($failExit -ne 1) { throw "Hook мав заблокувати коміт, але повернув $failExit." }
    if (-not $NoPause) { Read-Host 'Зроби скріншот FAIL, потім натисни Enter' | Out-Null }

    @(
        'RATES = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11}',
        '',
        'def demo_rate(value):',
        '    return RATES.get(value, 0)'
    ) | Set-Content -LiteralPath $demoFile -Encoding utf8

    git add -- $demoFile
    Write-Host ''
    Write-Host '=== PASS: коміт після рефакторингу через таблицю ===' -ForegroundColor Green
    Write-Host 'git commit -m "refactor: replace branches with lookup table"'
    git commit -m 'refactor: replace branches with lookup table' 2>&1 | Out-Host
    $passExit = $LASTEXITCODE
    Write-Host "Код завершення: $passExit"
    git log --oneline -2 | Out-Host
    if ($passExit -ne 0) { throw "Коміт після виправлення не пройшов: $passExit." }
    if (-not $NoPause) { Read-Host 'Зроби скріншот PASS, потім натисни Enter' | Out-Null }

    git switch $originalBranch | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Не вдалося повернутися на $originalBranch." }
    Write-Host ''
    Write-Host "Готово. Ти знову на гілці $originalBranch. Демонстрація збережена в $demoBranch."
}
finally {
    $env:LAB6_PYTHON = $oldPython
    Pop-Location
}
