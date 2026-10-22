# Starts the Flask app and a Cloudflare quick tunnel, then shows the public link.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = ".venv\Scripts\python.exe"
$toolsDir = Join-Path $PSScriptRoot ".tools"
$cloudflared = Join-Path $toolsDir "cloudflared.exe"
$log = Join-Path $toolsDir "tunnel.log"

if (-not (Test-Path $python)) {
    Write-Host "Setting up Python environment (first run only)..."
    python -m venv .venv
    & $python -m pip install -q -r requirements.txt
}

if (-not (Test-Path $cloudflared)) {
    Write-Host "Downloading cloudflared (first run only)..."
    New-Item -ItemType Directory -Force $toolsDir | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -OutFile $cloudflared `
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
}

Write-Host "Starting web server..."
$server = Start-Process $python -ArgumentList "app.py" -WindowStyle Hidden -PassThru

Write-Host "Starting tunnel..."
if (Test-Path $log) { Remove-Item $log }
$tunnel = Start-Process $cloudflared -ArgumentList "tunnel --no-autoupdate --url http://127.0.0.1:5000" `
    -RedirectStandardError $log -WindowStyle Hidden -PassThru

try {
    $url = $null
    for ($i = 0; $i -lt 60 -and -not $url; $i++) {
        Start-Sleep -Seconds 1
        if ($tunnel.HasExited) { throw "cloudflared stopped unexpectedly. See $log" }
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
            if ($m) { $url = $m.Matches[0].Value }
        }
    }
    if (-not $url) { throw "Could not get tunnel link. See $log" }

    Set-Clipboard $url
    Write-Host ""
    Write-Host "  ================================================" -ForegroundColor Red
    Write-Host "   Your site is live:" -ForegroundColor White
    Write-Host "   $url" -ForegroundColor Green
    Write-Host "   (copied to clipboard - share it with anyone)" -ForegroundColor Gray
    Write-Host "  ================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Keep this window open. Close it (or press Ctrl+C) to stop the site."
    Start-Process $url

    while (-not $tunnel.HasExited -and -not $server.HasExited) { Start-Sleep -Seconds 2 }
    if ($server.HasExited) { Write-Host "Web server stopped." -ForegroundColor Yellow }
    if ($tunnel.HasExited) { Write-Host "Tunnel stopped." -ForegroundColor Yellow }
}
finally {
    foreach ($p in @($tunnel, $server)) {
        if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    }
}
