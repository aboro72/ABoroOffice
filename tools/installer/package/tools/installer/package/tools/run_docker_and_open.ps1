$ErrorActionPreference = "Stop"

# Prefer the IPv4 address that has a default gateway (real LAN IP)
$ip = (Get-NetIPConfiguration `
    | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.IPv4Address -ne $null } `
    | Select-Object -First 1 -ExpandProperty IPv4Address `
    | Select-Object -ExpandProperty IPAddress)

# Fallback: first non-loopback IPv4 address
if (-not $ip) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 `
        | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } `
        | Select-Object -First 1 -ExpandProperty IPAddress)
}

if (-not $ip) {
    throw "No LAN IPv4 address found."
}

Write-Host "Starting docker compose..."
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    throw "docker compose failed with exit code $LASTEXITCODE"
}

$url = "http://$ip"

$adminUser = if ($env:DEMO_EXE_ADMIN_USERNAME) { $env:DEMO_EXE_ADMIN_USERNAME } else { "admin" }
$adminPass = if ($env:DEMO_EXE_PASSWORD) { $env:DEMO_EXE_PASSWORD } else { "demo1234" }

Write-Host ""
Write-Host "ABoroOffice is running:"
Write-Host "URL:      $url"
Write-Host "Admin:    $adminUser"
Write-Host "Password: $adminPass"
Write-Host ""
Write-Host "Opening $url"
Start-Process $url
