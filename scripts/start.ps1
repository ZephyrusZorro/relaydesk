$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function Invoke-Checked { param([string]$Program, [string[]]$Arguments) & $Program @Arguments; if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" } }
Invoke-Checked node @('scripts/configure.mjs')
Invoke-Checked node @('scripts/build-workflows.mjs')
Invoke-Checked docker @('compose','stop','worker','n8n')
Invoke-Checked docker @('compose','build','desk')
Invoke-Checked docker @('compose','run','--rm','--no-deps','--entrypoint','node','n8n','/opt/relaydesk/scripts/n8n-init.mjs')
Invoke-Checked docker @('compose','up','-d','--wait','desk','n8n','worker')
Invoke-Checked node @('scripts/print-urls.mjs')
