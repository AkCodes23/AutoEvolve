# AutoEvolve 1-Line Zero-Dependency Installer (Windows PowerShell)
# Usage:
#   irm https://raw.githubusercontent.com/AkCodes23/AutoEvolve/lean/mindset-only/install.ps1 | iex
#   .\install.ps1 [-TargetDir <path>] [-Force]

param (
    [string]$TargetDir = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://raw.githubusercontent.com/AkCodes23/AutoEvolve/lean/mindset-only"
$ResolvedTarget = (Resolve-Path -LiteralPath $TargetDir).Path

Write-Host "=== AutoEvolve Installer ===" -ForegroundColor Cyan
Write-Host "Target directory: $ResolvedTarget"

function Install-File {
    param (
        [string]$RelativeSrc,
        [string]$RelativeDst
    )

    $DestinationPath = Join-Path -Path $ResolvedTarget -ChildPath $RelativeDst
    $DestinationDir = Split-Path -Path $DestinationPath -Parent

    if ((Test-Path -LiteralPath $DestinationPath) -and (-not $Force)) {
        Write-Host "  [skip] $RelativeDst already exists (use -Force to overwrite)" -ForegroundColor DarkGray
        return
    }

    if (-not (Test-Path -LiteralPath $DestinationDir)) {
        New-Item -ItemType Directory -LiteralPath $DestinationDir -Force | Out-Null
    }

    $LocalSourcePath = Join-Path -Path $PSScriptRoot -ChildPath $RelativeSrc

    if ($PSScriptRoot -and (Test-Path -LiteralPath $LocalSourcePath)) {
        Copy-Item -LiteralPath $LocalSourcePath -Destination $DestinationPath -Force
    } else {
        $DownloadUrl = "$RepoUrl/$RelativeSrc"
        Invoke-RestMethod -Uri $DownloadUrl -OutFile $DestinationPath
    }

    Write-Host "  [+] Installed $RelativeDst" -ForegroundColor Green
}

# 1. Core Mindset & Conventions
Install-File "AGENTS.md" "AGENTS.md"
Install-File "DIRECTION.md" "DIRECTION.md"
Install-File "JOURNAL.md" "JOURNAL.md"

# 2. Detect IDEs and Install Specific Adapters
$InstalledAdapter = $false

if ((Test-Path -LiteralPath (Join-Path $ResolvedTarget ".cursor")) -or (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".cursorrules"))) {
    Install-File "adapters/cursor.mdc" ".cursor/rules/autoevolve.mdc"
    $InstalledAdapter = $true
}

if ((Test-Path -LiteralPath (Join-Path $ResolvedTarget ".windsurfrules")) -or (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".windsurf"))) {
    Install-File "adapters/windsurf.md" ".windsurfrules"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".github")) {
    Install-File "adapters/copilot-instructions.md" ".github/copilot-instructions.md"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".clinerules")) {
    Install-File "adapters/cline.md" ".clinerules"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".continue")) {
    Install-File "adapters/continue.md" ".continue/prompts/autoevolve.prompt"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".zed")) {
    Install-File "adapters/zed.md" ".zed/rules.md"
    $InstalledAdapter = $true
}

if ((Test-Path -LiteralPath (Join-Path $ResolvedTarget ".idea")) -or (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".jetbrains"))) {
    Install-File "adapters/jetbrains.md" ".jetbrains/ai-instructions.md"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".cody")) {
    Install-File "adapters/cody.md" ".cody/instructions.md"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".openhands")) {
    Install-File "adapters/openhands.md" ".openhands/instructions.md"
    $InstalledAdapter = $true
}

if (Test-Path -LiteralPath (Join-Path $ResolvedTarget ".gemini")) {
    Install-File "adapters/gemini.md" "GEMINI.md"
    $InstalledAdapter = $true
}

if (-not $InstalledAdapter) {
    # Default: install Claude/generic adapter as CLAUDE.md
    Install-File "adapters/claude.md" "CLAUDE.md"
}

Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host "AutoEvolve mindset installed successfully." -ForegroundColor Green
Write-Host "   Next steps:"
Write-Host "   1. Set your goal and verification command in DIRECTION.md"
Write-Host "   2. Prompt your AI coding agent to start evolving!"
