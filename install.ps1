param(
    [string]$TargetDir = ".",
    [string[]]$Agents = @("generic", "claude"),
    [switch]$Force,
    [string]$Ref = $env:AUTOEVOLVE_REF,
    [switch]$ListAgents
)

$ErrorActionPreference = "Stop"
$SourceDir = $null
if ($PSScriptRoot -and -not $Ref) {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot "adapters/manifest.txt")) { $SourceDir = $PSScriptRoot }
}
$Target = (Resolve-Path -LiteralPath $TargetDir).Path
$Utf8 = New-Object System.Text.UTF8Encoding $false

function Assert-RelativePath([string]$Path) {
    if ($Path -notmatch '^[a-zA-Z0-9_./-]+$' -or $Path.StartsWith("/") -or
        $Path -match '(^|/)\.\.?(/|$)|//') { throw "Invalid distribution path: $Path" }
}
function Assert-SafeTarget([string]$Path) {
    $Current = $Target
    foreach ($Part in $Path.Split("/")) {
        $Current = Join-Path $Current $Part
        if (Test-Path -LiteralPath $Current) {
            $Item = Get-Item -LiteralPath $Current -Force
            if ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                throw "Refusing symbolic link or junction: $Current"
            }
        }
    }
}
function Get-Digest([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-Download([string]$Url, [string]$Destination, [string]$Accept = "text/plain") {
    Invoke-RestMethod -Uri $Url -OutFile $Destination -TimeoutSec 60 -Headers @{ Accept = $Accept }
}

Assert-SafeTarget ".autoevolve"
$State = Join-Path $Target ".autoevolve"
[System.IO.Directory]::CreateDirectory($State) | Out-Null
$Lock = Join-Path $State "install.lock"
New-Item -ItemType Directory -Path $Lock -ErrorAction Stop | Out-Null
$Stage = Join-Path $State ("staging." + [guid]::NewGuid().ToString("N"))
$Temporary = $null
try {
    [System.IO.Directory]::CreateDirectory($Stage) | Out-Null
    if (-not $SourceDir) {
        if (-not $Ref) {
            $RefFile = Join-Path $Stage "ref"
            try {
                Get-Download "https://api.github.com/repos/AkCodes23/AutoEvolve/commits/main" $RefFile "application/vnd.github.sha"
            } catch {
                throw "Could not resolve main. Retry with -Ref FULL_COMMIT_SHA or install from a local checkout. $($_.Exception.Message)"
            }
            $Ref = [System.IO.File]::ReadAllText($RefFile).Trim()
        }
        if ($Ref -notmatch '^[a-fA-F0-9]{40}$') { throw "Ref must be a full 40-character commit SHA." }
        $RepoUrl = "https://raw.githubusercontent.com/AkCodes23/AutoEvolve/$Ref"
        $Guide = "https://github.com/AkCodes23/AutoEvolve/blob/$Ref/docs/adapters.md"
        Write-Host "Distribution commit: $Ref"
    } else {
        $Guide = Join-Path $SourceDir "docs/adapters.md"
        Write-Host "Distribution directory: $SourceDir"
    }

    function Get-DistributionFile([string]$Path) {
        Assert-RelativePath $Path
        $Staged = Join-Path $Stage $Path
        [System.IO.Directory]::CreateDirectory((Split-Path $Staged -Parent)) | Out-Null
        if ($SourceDir) { Copy-Item -LiteralPath (Join-Path $SourceDir $Path) -Destination $Staged }
        else { Get-Download "$RepoUrl/$Path" $Staged }
    }
    function Assert-Checksum([string]$Path) {
        if (-not $Checksums.ContainsKey($Path) -or
            $Checksums[$Path] -ne (Get-Digest (Join-Path $Stage $Path))) {
            throw "Checksum mismatch for $Path. Retry or regenerate the local distribution."
        }
    }
    Get-DistributionFile "checksums.txt"
    $Checksums = @{}
    foreach ($Line in Get-Content -LiteralPath (Join-Path $Stage "checksums.txt")) {
        if ($Line -notmatch '^([a-f0-9]{64})  (.+)$') { throw "Invalid checksum manifest." }
        $Checksums[$Matches[2]] = $Matches[1]
    }
    Get-DistributionFile "adapters/manifest.txt"
    Assert-Checksum "adapters/manifest.txt"
    $Manifest = @(Import-Csv -LiteralPath (Join-Path $Stage "adapters/manifest.txt") -Delimiter "|" -Header Id, Source, Destination, Activation, Status)
    foreach ($Adapter in $Manifest) {
        Assert-RelativePath $Adapter.Source
        Assert-RelativePath $Adapter.Destination
        if ($Adapter.Id -notmatch '^[a-z][a-z-]*$' -or
            $Adapter.Activation -notin @("automatic", "manual") -or
            $Adapter.Status -notin @("documented", "experimental")) { throw "Invalid adapter manifest." }
    }
    if ($ListAgents) { $Manifest | Format-Table; return }
    $Selected = @($Agents -split "," | Sort-Object -Unique)
    foreach ($Agent in $Selected) {
        if ($Agent -cnotin $Manifest.Id) { throw "Unknown agent '$Agent'; use -ListAgents." }
    }
    $Plan = @()
    foreach ($File in @("DIRECTION.md", "JOURNAL.md", "CONSTRAINTS.md")) {
        Get-DistributionFile $File
        Assert-Checksum $File
        $Plan += [pscustomobject]@{ Source = $File; Destination = $File; Kind = "state" }
    }
    foreach ($Adapter in $Manifest) {
        if ($Adapter.Id -cnotin $Selected) { continue }
        Get-DistributionFile $Adapter.Source
        Assert-Checksum $Adapter.Source
        $Plan += [pscustomobject]@{ Source = $Adapter.Source; Destination = $Adapter.Destination; Kind = "engine" }
        Write-Host "Selected $($Adapter.Id) ($($Adapter.Status); $($Adapter.Activation) activation): $($Adapter.Destination)"
    }
    $Conflicts = 0
    foreach ($Entry in $Plan) {
        Assert-SafeTarget $Entry.Destination
        $ReceiptRelative = ".autoevolve/receipts/$($Entry.Destination).sha256"
        Assert-SafeTarget $ReceiptRelative
        $Receipt = Join-Path $Target $ReceiptRelative
        $Destination = Join-Path $Target $Entry.Destination
        $Staged = Join-Path $Stage $Entry.Source
        $Blocked = $false
        $Parent = Split-Path $Destination -Parent
        while ($Parent -and $Parent -ne $Target) {
            if ((Test-Path -LiteralPath $Parent) -and -not (Test-Path -LiteralPath $Parent -PathType Container)) {
                $Blocked = $true
                break
            }
            $Parent = Split-Path $Parent -Parent
        }
        if ($Blocked -or ((Test-Path -LiteralPath $Destination) -and -not (Test-Path -LiteralPath $Destination -PathType Leaf))) {
            Write-Host "[manual integration required] $($Entry.Destination) (an existing file or directory blocks this path)"
            $Conflicts++
            continue
        }
        if ((Test-Path -LiteralPath $Destination) -and $Entry.Kind -eq "state") {
            Write-Host "[preserved] $($Entry.Destination)"
            continue
        }
        $Digest = Get-Digest $Staged
        $Previous = $null
        if (Test-Path -LiteralPath $Destination) { $Previous = Get-Digest $Destination }
        if ($Previous -and $Previous -ne $Digest) {
            if (-not $Force -or -not (Test-Path -LiteralPath $Receipt) -or
                [System.IO.File]::ReadAllText($Receipt).Trim() -ne $Previous) {
                Write-Host "[manual integration required] $($Entry.Destination) (existing contents preserved)"
                $Conflicts++
                continue
            }
        }
        if ($Previous -eq $Digest) { Write-Host "[current] $($Entry.Destination)" }
        else {
            [System.IO.Directory]::CreateDirectory((Split-Path $Destination -Parent)) | Out-Null
            $Temporary = Join-Path (Split-Path $Destination -Parent) (".autoevolve." + [guid]::NewGuid().ToString("N"))
            [System.IO.File]::Copy($Staged, $Temporary)
            if ($Previous) {
                Assert-SafeTarget ".autoevolve/backups"
                $BackupDir = Join-Path $State ("backups/upgrade." + [guid]::NewGuid().ToString("N"))
                [System.IO.Directory]::CreateDirectory($BackupDir) | Out-Null
                $Backup = Join-Path $BackupDir (Split-Path $Destination -Leaf)
                [System.IO.File]::Replace($Temporary, $Destination, $Backup)
                Write-Host "[backup] $Backup"
            } else { [System.IO.File]::Move($Temporary, $Destination) }
            $Temporary = $null
            Write-Host "[installed] $($Entry.Destination)"
        }
        if ($Entry.Kind -eq "engine") {
            [System.IO.Directory]::CreateDirectory((Split-Path $Receipt -Parent)) | Out-Null
            $ReceiptStage = Join-Path $Stage "receipt"
            [System.IO.File]::WriteAllText($ReceiptStage, "$Digest`n", $Utf8)
            if (Test-Path -LiteralPath $Receipt) {
                [System.IO.File]::Replace($ReceiptStage, $Receipt, (Join-Path $Stage "old-receipt"))
            }
            else { [System.IO.File]::Move($ReceiptStage, $Receipt) }
        }
    }
    if ($Conflicts) {
        Write-Host "Installation needs manual integration for $Conflicts file(s). No conflicting files were replaced."
        Write-Host "Compare the selected adapter with your existing instructions; see $Guide"
        exit 2
    }
    Write-Host "Files installed or already current. This does not verify agent activation."
    Write-Host "Follow the selected agent's activation check at $Guide, then complete DIRECTION.md."
} finally {
    if ($Temporary -and (Test-Path -LiteralPath $Temporary)) { Remove-Item -LiteralPath $Temporary -Force }
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
    Remove-Item -LiteralPath $Lock
}
