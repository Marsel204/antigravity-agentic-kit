$ErrorActionPreference = 'Stop'
$entry = Join-Path $PSScriptRoot 'scripts/aek.py'
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $entry install @args
} else {
    & python $entry install @args
}
exit $LASTEXITCODE
