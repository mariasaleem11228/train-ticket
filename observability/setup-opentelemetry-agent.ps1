param(
    [string]$Destination = (Join-Path $PSScriptRoot 'opentelemetry-javaagent.jar')
)

$ErrorActionPreference = 'Stop'
$version = '2.31.0'
$expectedSha256 = 'D48673B2FF956B26D809BC34243649913D4EEFD9191C4E175B686DA633E0134B'
$url = "https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v$version/opentelemetry-javaagent.jar"

if (-not (Test-Path -LiteralPath $Destination)) {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $Destination
}

$actual = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
if ($actual -ne $expectedSha256) {
    throw "OpenTelemetry agent checksum mismatch. Expected $expectedSha256 but found $actual"
}

Write-Output "OpenTelemetry Java agent $version verified: $actual"
