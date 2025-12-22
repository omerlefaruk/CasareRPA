[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OrchestratorUrl,

    [Parameter(Mandatory = $true)]
    [string]$RobotId,

    [Parameter(Mandatory = $true)]
    [string]$RobotApiKey,

    [Parameter(Mandatory = $false)]
    [string]$RobotName = $env:COMPUTERNAME,

    [Parameter(Mandatory = $false)]
    [ValidateSet('Machine', 'User')]
    [string]$Scope = 'Machine',

    [Parameter(Mandatory = $false)]
    [string]$PythonExe = 'python',

    [Parameter(Mandatory = $false)]
    [switch]$StartRobotAgent
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Set-EnvVar {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][ValidateSet('Machine', 'User')][string]$Target
    )

    [Environment]::SetEnvironmentVariable($Name, $Value, $Target)
    $env:$Name = $Value
}

function Ensure-AdminIfMachineScope {
    param([Parameter(Mandatory = $true)][string]$Target)

    if ($Target -ne 'Machine') {
        return
    }

    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        throw "Scope=Machine requires an elevated PowerShell (Run as Administrator). Use -Scope User or re-run elevated."
    }
}

Ensure-AdminIfMachineScope -Target $Scope

$normalizedUrl = $OrchestratorUrl.TrimEnd('/')

Write-Host "Configuring Casare Robot Agent environment variables ($Scope)..."
Set-EnvVar -Name 'CASARE_ORCHESTRATOR_URL' -Value $normalizedUrl -Target $Scope
Set-EnvVar -Name 'CASARE_ORCHESTRATOR_API_KEY' -Value $RobotApiKey -Target $Scope
Set-EnvVar -Name 'CASARE_ROBOT_ID' -Value $RobotId -Target $Scope
Set-EnvVar -Name 'CASARE_ROBOT_NAME' -Value $RobotName -Target $Scope

# Back-compat for older agent versions / alternate config names.
Set-EnvVar -Name 'ORCHESTRATOR_URL' -Value $normalizedUrl -Target $Scope
Set-EnvVar -Name 'ORCHESTRATOR_API_KEY' -Value $RobotApiKey -Target $Scope

Write-Host "OK: Env configured."
Write-Host "- CASARE_ORCHESTRATOR_URL=$normalizedUrl"
Write-Host "- CASARE_ROBOT_ID=$RobotId"
Write-Host "- CASARE_ROBOT_NAME=$RobotName"

if ($StartRobotAgent) {
    Write-Host "Starting Robot Agent..."

    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
    $managePy = Join-Path $repoRoot 'manage.py'

    if (-not (Test-Path $managePy)) {
        throw "Could not find manage.py at $managePy. Run this script from the CasareRPA repo checkout, or update the script to point to your installed agent entrypoint."
Write-Host "  $PythonExe $managePy robot start"

    & $PythonExe $managePy robot start
    exit $LASTEXITCODE
}

Write-Host "Done. To start the agent manually:"
Write-Host "  $PythonExe ..\manage.py robot start"
