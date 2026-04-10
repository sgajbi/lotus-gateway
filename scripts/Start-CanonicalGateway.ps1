param(
  [int]$Port = 8111,
  [string]$ListenHost = "0.0.0.0",
  [switch]$Foreground
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = if (Test-Path (Join-Path $repoRoot ".venv\\Scripts\\python.exe")) {
  Join-Path $repoRoot ".venv\\Scripts\\python.exe"
} else {
  "C:\\Python313\\python.exe"
}

$arguments = @(
  "-m", "uvicorn",
  "app.main:app",
  "--app-dir", "src",
  "--host", $ListenHost,
  "--port", "$Port"
)

if ($Foreground) {
  Push-Location $repoRoot
  try {
    & $python @arguments
    exit $LASTEXITCODE
  } finally {
    Pop-Location
  }
}

try {
  $existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
    Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($pid in $existing) {
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
  }
} catch {
}

$stdout = Join-Path $repoRoot "gateway-$Port.out.log"
$stderr = Join-Path $repoRoot "gateway-$Port.err.log"
try { if (Test-Path $stdout) { Remove-Item $stdout -Force -ErrorAction Stop } } catch {}
try { if (Test-Path $stderr) { Remove-Item $stderr -Force -ErrorAction Stop } } catch {}

Start-Process -FilePath $python `
  -ArgumentList $arguments `
  -WorkingDirectory $repoRoot `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr | Out-Null

Start-Sleep -Seconds 5
$response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health/ready" -UseBasicParsing -TimeoutSec 15
if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
  throw "Gateway canonical startup failed on port $Port."
}

Write-Host "Gateway canonical startup ready on http://127.0.0.1:$Port"
