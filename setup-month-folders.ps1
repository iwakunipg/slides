# PowerShell スクリプト: setup-month-folders.ps1

# 基本パス
$basePath = "slides/2025"

# フォルダ作成開始
Write-Host "Creating monthly folders under $basePath..."

# 01〜12 のフォルダを作成
1..12 | ForEach-Object {
    $month = $_.ToString("D2")  # "01", "02", ..., "12"
    $folderPath = Join-Path $basePath $month
    if (-not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath | Out-Null
        Write-Host "✅ Created folder: $folderPath"
    } else {
        Write-Host "⚠️ Already exists: $folderPath"
    }
}

Write-Host "🎉 Monthly folders created!"
