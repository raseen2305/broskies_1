# PowerShell script to resolve ALL Git merge conflicts

function Resolve-GitConflicts {
    param([string]$content)
    
    $lines = $content -split "`n"
    $result = @()
    $inConflict = $false
    $keepSection = $false
    
    foreach ($line in $lines) {
        if ($line -match '^<<<<<<< HEAD') {
            $inConflict = $true
            $keepSection = $true
            continue
        }
        elseif ($line -match '^=======') {
            $keepSection = $false
            continue
        }
        elseif ($line -match '^>>>>>>> ') {
            $inConflict = $false
            $keepSection = $false
            continue
        }
        
        if (-not $inConflict -or $keepSection) {
            $result += $line
        }
    }
    
    return ($result -join "`n")
}

# Find all files with conflicts
$files = Get-ChildItem -Recurse -Include *.ts,*.tsx,*.js,*.jsx,*.py -File | Where-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    $content -match '<<<<<<< HEAD'
}

Write-Host "Found $($files.Count) files with conflicts"
Write-Host ""

foreach ($file in $files) {
    Write-Host "Processing $($file.FullName)..."
    
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $resolved = Resolve-GitConflicts -content $content
    [System.IO.File]::WriteAllText($file.FullName, $resolved, [System.Text.UTF8Encoding]::new($false))
    
    Write-Host "  Resolved"
}

Write-Host ""
Write-Host "All conflicts resolved!"
