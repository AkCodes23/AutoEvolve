<#
.SYNOPSIS
AutoEvolve PowerShell installer for Windows environments.

.DESCRIPTION
Run this script from a reviewed release checkout:
  .\install.ps1 -Target C:\path\to\your\repo

It never executes a remote script, never overwrites an existing file, and reports
every skipped file so users do not mistake a partial installation for a completed one.

.PARAMETER Target
Target directory where AutoEvolve instructions should be installed. Defaults to current directory.

.PARAMETER Profile
Mindset profile to install: 'core' (condensed, default) or 'full' (complete AGENTS.md).

.PARAMETER DryRun
If set, previews files that would be created without writing any files.
#>

[CmdletBinding()]
param (
    [Parameter(Position=0)]
    [string]$Target = (Get-Location).Path,

    [Parameter()]
    [ValidateSet("core", "full")]
    [string]$Profile = "core",

    [Parameter()]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$SourceDir = $PSScriptRoot
if (-not $SourceDir) {
    $SourceDir = (Get-Location).Path
}

if (-not (Test-Path -Path (Join-Path $SourceDir "AGENTS.md")) -or -not (Test-Path -Path (Join-Path $SourceDir "adapters\_core.md"))) {
    Write-Error "Installer source is incomplete. Download a release checkout; do not pipe this script from a URL."
    exit 65
}

if (-not (Test-Path -Path $Target)) {
    Write-Error "Target directory does not exist: $Target"
    exit 66
}

$TargetDir = (Get-Item -Path $Target).FullName

$script:CanonicalSkipped = $false
$script:OtherSkipped = $false
$script:Written = $false

$AgentsPath = Join-Path $TargetDir "AGENTS.md"
$script:CanonicalPresent = $false
if (Test-Path -Path $AgentsPath) {
    $content = Get-Content -Path $AgentsPath -ErrorAction SilentlyContinue
    if ($content -match 'AutoEvolve-Core' -or $content -match '^#+\s+AutoEvolve') {
        $script:CanonicalPresent = $true
    }
}

function Install-AutoEvolveFile {
    param (
        [string]$SourceRel,
        [string]$DestinationRel,
        [bool]$IsCanonical = $false
    )

    $sourceFile = Join-Path $SourceDir $SourceRel
    $destFile = Join-Path $TargetDir $DestinationRel

    if (-not (Test-Path -Path $sourceFile)) {
        Write-Error "Missing installer source: $SourceRel"
        exit 65
    }

    if (Test-Path -Path $destFile) {
        Write-Host "  skip $DestinationRel (already exists; no overwrite)"
        if ($IsCanonical) { $script:CanonicalSkipped = $true } else { $script:OtherSkipped = $true }
        return
    }

    if ($DryRun) {
        Write-Host "  would write $DestinationRel"
        return
    }

    $destDir = Split-Path -Path $destFile -Parent
    if (-not (Test-Path -Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    $tempFile = Join-Path $destDir (".autoevolve-install-$PID-$([System.IO.Path]::GetRandomFileName()).tmp")
    try {
        Copy-Item -Path $sourceFile -Destination $tempFile -Force
        if (-not (Test-Path -Path $destFile)) {
            Move-Item -Path $tempFile -Destination $destFile -ErrorAction Stop
            Write-Host "  wrote $DestinationRel"
            $script:Written = $true
        } else {
            Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
            Write-Host "  skip $DestinationRel (created concurrently; no overwrite)"
            if ($IsCanonical) { $script:CanonicalSkipped = $true } else { $script:OtherSkipped = $true }
        }
    } catch {
        if (Test-Path -Path $tempFile) { Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue }
        throw $_
    }
}

Write-Host "AutoEvolve: source=$SourceDir target=$TargetDir"
$CanonicalSource = if ($Profile -eq "full") { "AGENTS.md" } else { "adapters\_core.md" }
Write-Host "AutoEvolve profile: $Profile"

Install-AutoEvolveFile -SourceRel $CanonicalSource -DestinationRel "AGENTS.md" -IsCanonical $true

if ((Test-Path -Path (Join-Path $TargetDir ".claude")) -or (Test-Path -Path (Join-Path $TargetDir "CLAUDE.md"))) {
    Install-AutoEvolveFile -SourceRel "adapters\claude.md" -DestinationRel "CLAUDE.md"
}

if (Test-Path -Path (Join-Path $TargetDir ".cursor")) {
    Install-AutoEvolveFile -SourceRel "adapters\cursor.mdc" -DestinationRel ".cursor\rules\autoevolve.mdc"
}

if (Test-Path -Path (Join-Path $TargetDir ".windsurf")) {
    Install-AutoEvolveFile -SourceRel "adapters\windsurf.md" -DestinationRel ".windsurf\rules\autoevolve.md"
}

if (Test-Path -Path (Join-Path $TargetDir ".github")) {
    Install-AutoEvolveFile -SourceRel "adapters\copilot-instructions.md" -DestinationRel ".github\copilot-instructions.md"
}

if ($DryRun) {
    Write-Host "Dry run complete. No files changed."
    exit 0
}

if ($script:CanonicalSkipped -and $script:CanonicalPresent) {
    Write-Host "AGENTS.md already carries AutoEvolve; left untouched."
    if ($script:Written) {
        Write-Host "Tool adapters listed above were added alongside it."
    }
    Write-Host "Already installed. Nothing to merge."
    exit 0
}

if ($script:CanonicalSkipped) {
    Write-Error "Manual merge required: AGENTS.md already exists in the target and does not carry AutoEvolve."
    Write-Host "Review $SourceDir\$CanonicalSource and merge it under a clear heading, then rerun -DryRun to inspect adapters."
    if ($script:Written) {
        Write-Host "Note: the tool adapters listed above WERE written and are already active for those tools."
        Write-Host "Only AGENTS.md still needs merging."
    } else {
        Write-Host "Nothing was written; AutoEvolve is not active in this target."
    }
    exit 2
}

if ($script:OtherSkipped) {
    Write-Host "Installed canonical AGENTS.md, but one or more tool adapters were skipped. Review the messages above."
}

if ($script:Written) {
    Write-Host "Installation complete. Review the added files before relying on them in an agent session."
} else {
    Write-Host "No files were written."
}
