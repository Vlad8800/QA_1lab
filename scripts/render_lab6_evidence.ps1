# Render captured, unedited command output as readable PNG evidence.
Add-Type -AssemblyName System.Drawing
$evidenceDir = Join-Path $PSScriptRoot '..\docs\lab6\evidence'
Get-ChildItem -LiteralPath $evidenceDir -Filter '*.txt' | ForEach-Object {
    $lines = @(Get-Content -LiteralPath $_.FullName | ForEach-Object { $_ -replace '\x1b\[[0-9;]*m', '' })
    $font = [System.Drawing.Font]::new('Consolas', 13)
    $width = [Math]::Max(980, [Math]::Min(2200, 28 + (($lines | ForEach-Object Length | Measure-Object -Maximum).Maximum * 9)))
    $height = [Math]::Max(100, 30 + $lines.Count * 23)
    $bitmap = [System.Drawing.Bitmap]::new($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::FromArgb(20, 24, 31))
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $color = [System.Drawing.Color]::FromArgb(230, 235, 240)
        if ($lines[$i] -match '\[FAIL\]|\[BLOCKED\]|exit=1') {
            $color = [System.Drawing.Color]::FromArgb(255, 105, 105)
        } elseif ($lines[$i] -match '\[PASS\]|exit=0|CC=1') {
            $color = [System.Drawing.Color]::FromArgb(114, 220, 145)
        }
        $brush = [System.Drawing.SolidBrush]::new($color)
        $graphics.DrawString($lines[$i], $font, $brush, 12, 10 + $i * 23)
        $brush.Dispose()
    }
    $destination = [System.IO.Path]::ChangeExtension($_.FullName, '.png')
    $bitmap.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    $font.Dispose()
    Write-Output $destination
}
