function Invoke-RestMethod {
    param([string]$Uri, [string]$OutFile, [int]$TimeoutSec, [hashtable]$Headers)
    [System.IO.File]::AppendAllText($env:REQUEST_LOG, "$Uri`n")
    if ($Uri.Contains("/commits/main")) {
        if ($env:FAIL_RESOLVE -eq "1") { throw "Simulated rate limit" }
        [System.IO.File]::WriteAllText($OutFile, ("a" * 40))
        return
    }
    $Relative = ($Uri -split "/AutoEvolve/", 2)[1] -replace "^[^/]+/", ""
    if ($Relative -eq $env:FAIL_FILE) {
        [System.IO.File]::WriteAllText($OutFile, "partial download")
        if ($env:CORRUPT_FILE -ne "1") { throw "Simulated interrupted transfer" }
        return
    }
    [System.IO.File]::Copy((Join-Path $env:FIXTURE_SOURCE $Relative), $OutFile, $true)
}
