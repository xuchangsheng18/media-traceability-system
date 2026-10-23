[CmdletBinding()]
param(
    [ValidateSet('help','setup','dev','stop','status','lint','format-check','type-check','test','contract-test','integration-test','build','security-scan','clean','pre-commit','ci')]
    [string]$Command = 'help',
    [ValidateSet('server','local')][string]$Target = 'server',
    [switch]$DryRun, [switch]$Tools, [switch]$Apply, [switch]$AllowStackChanges
)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskProfile = Get-Content -LiteralPath (Join-Path $taskRoot 'config/stage-three-profile.json') -Raw | ConvertFrom-Json
$Command = $Command.ToLowerInvariant()
$taskArguments = @('scripts/dev.py', $Command)
if ($DryRun) { $taskArguments += '--dry-run' }
if ($Tools) { $taskArguments += '--tools' }
if ($Apply) { $taskArguments += '--apply' }
if ($AllowStackChanges) { $taskArguments += '--allow-stack-changes' }
if ($Target -eq 'server') {
    # The profile contains only fixed project paths; never interpolate credentials or arbitrary commands.
    if ($taskProfile.server_alias -notmatch '^[A-Za-z0-9._-]+$' -or $taskProfile.server_repository -notmatch '^/[A-Za-z0-9/_-]+$' -or $taskProfile.python_executable -notmatch '^/[A-Za-z0-9/._-]+$') { throw 'Invalid server profile paths' }
    $taskRemote = 'cd ' + $taskProfile.server_repository + ' && ' + $taskProfile.python_executable + ' ' + ($taskArguments -join ' ')
    & ssh -o BatchMode=yes -- $taskProfile.server_alias $taskRemote
} else {
    if (-not $env:MT_PYTHON -or -not (Test-Path -LiteralPath $env:MT_PYTHON -PathType Leaf)) { throw 'Local mode requires an explicit MT_PYTHON pointing to a separately prepared locked Python 3.11.17 environment. Use the default server target for the existing Miniforge py311.' }
    Push-Location -LiteralPath $taskRoot
    try { & $env:MT_PYTHON @taskArguments } finally { Pop-Location }
}
exit $LASTEXITCODE
