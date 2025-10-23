function Check-Project {
    Write-Host "=== MAA Project Structure Check ===" -ForegroundColor Cyan
    
    # Check directory structure
    $requiredDirs = @(
        "deps",
        "assets", 
        "assets/MaaCommonAssets",
        "assets/MaaCommonAssets/OCR"
    )
    
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            Write-Host "OK $dir exists" -ForegroundColor Green
            $items = Get-ChildItem $dir
            Write-Host "   Contains $($items.Count) items"
        } else {
            Write-Host "FAIL $dir missing" -ForegroundColor Red
        }
    }
    
    # Check critical files
    Write-Host "`n=== Critical Files Check ===" -ForegroundColor Cyan
    
    # Check interface.json in both locations
    $interfacePaths = @("interface.json", "assets/interface.json")
    $interfaceFound = $false
    
    foreach ($path in $interfacePaths) {
        if (Test-Path $path) {
            Write-Host "OK $path exists" -ForegroundColor Green
            try {
                $content = Get-Content $path -Raw | ConvertFrom-Json
                Write-Host "  JSON format is valid"
                $interfaceFound = $true
            } catch {
                Write-Host "  JSON format error: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    if (-not $interfaceFound) {
        Write-Host "FAIL No valid interface.json found" -ForegroundColor Red
    }
    
    # Check MaaFramework headers
    Write-Host "`n=== MaaFramework Headers ===" -ForegroundColor Cyan
    $headers = Get-ChildItem "deps/include/MaaFramework" -Filter *.h
    if ($headers) {
        Write-Host "OK Found $($headers.Count) header files:" -ForegroundColor Green
        $headers | ForEach-Object { Write-Host "  - $($_.Name)" }
    } else {
        Write-Host "FAIL No header files found" -ForegroundColor Red
    }
    
    # Check OCR models
    Write-Host "`n=== OCR Models Check ===" -ForegroundColor Cyan
    $ocrDirs = Get-ChildItem "assets/MaaCommonAssets/OCR" -Directory
    if ($ocrDirs) {
        Write-Host "OK Found OCR versions:" -ForegroundColor Green
        $ocrDirs | ForEach-Object { Write-Host "  - $($_.Name)" }
    } else {
        Write-Host "FAIL No OCR models found" -ForegroundColor Red
    }
}

Check-Project