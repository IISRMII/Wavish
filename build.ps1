# Builds a portable Wavish.exe with bundled ffmpeg.
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BinDir = Join-Path $Root "bin"

function Ensure-Ffmpeg {
    $ffmpeg = Join-Path $BinDir "ffmpeg.exe"
    if (Test-Path $ffmpeg) {
        Write-Host "ffmpeg already present."
        return
    }

    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $zipPath = Join-Path $env:TEMP "ffmpeg-essentials.zip"
    $extractDir = Join-Path $env:TEMP "ffmpeg-extract"

    Write-Host "Downloading ffmpeg essentials..."
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $found = Get-ChildItem -Path $extractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if (-not $found) { throw "ffmpeg.exe not found in downloaded archive." }

    Copy-Item $found.FullName $ffmpeg -Force
    Write-Host "Bundled ffmpeg to $ffmpeg"
}

Set-Location $Root

if (-not (Test-Path "venv")) {
    python -m venv venv
}

$python = Join-Path $Root "venv\Scripts\python.exe"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install --python $python -r requirements.txt
} else {
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}
Ensure-Ffmpeg

& ".\venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name Wavish `
    --add-data "bin\ffmpeg.exe;bin" `
    --collect-all yt_dlp `
    --collect-all curl_cffi `
    app.py
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Done: dist\Wavish.exe"
Write-Host "Copy dist\Wavish.exe anywhere. settings.json is created beside it on first run."
