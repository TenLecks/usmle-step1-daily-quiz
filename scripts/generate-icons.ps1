Add-Type -AssemblyName System.Drawing

function New-Icon {
    param([int]$Size, [string]$Path)
    $bmp = New-Object System.Drawing.Bitmap($Size, $Size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $bg = [System.Drawing.Color]::FromArgb(255, 37, 99, 235)  # #2563eb
    $g.Clear($bg)
    $fontSize = [int]($Size * 0.42)
    $font = New-Object System.Drawing.Font("Arial", $fontSize, [System.Drawing.FontStyle]::Bold)
    $brush = [System.Drawing.Brushes]::White
    $fmt = New-Object System.Drawing.StringFormat
    $fmt.Alignment = [System.Drawing.StringAlignment]::Center
    $fmt.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, 0, $Size, $Size)
    $g.DrawString("Q1", $font, $brush, $rect, $fmt)
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

$iconDir = Join-Path $PSScriptRoot "..\docs\icons"
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
New-Icon -Size 192 -Path (Join-Path $iconDir "icon-192.png")
New-Icon -Size 512 -Path (Join-Path $iconDir "icon-512.png")
New-Icon -Size 180 -Path (Join-Path $iconDir "apple-touch-icon.png")
Write-Host "Icons written to $iconDir"
