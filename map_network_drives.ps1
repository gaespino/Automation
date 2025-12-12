# Map Network Drives Script
# This script maps network drives I, Q, R, and S to their respective network paths

Write-Host "Mapping network drives..." -ForegroundColor Cyan

# Define drive mappings
$driveMappings = @(
    @{ Letter = "I:"; Path = "\\Amr\ec\proj\mdl\cr\intel" },
    @{ Letter = "Q:"; Path = "\\crcv03a-cifs.cr.intel.com\mpe_spr_003" },
    @{ Letter = "R:"; Path = "\\crcv03a-cifs.cr.intel.com\mfg_tlo_001" },
    @{ Letter = "S:"; Path = "\\crcv03a-cifs.cr.intel.com\mfg_tlo_002" }
)

# Map each drive
foreach ($mapping in $driveMappings) {
    $driveLetter = $mapping.Letter
    $networkPath = $mapping.Path
    
    try {
        # Check if drive is already mapped
        if (Test-Path $driveLetter) {
            Write-Host "Drive $driveLetter is already mapped" -ForegroundColor Yellow
        }
        else {
            # Map the network drive (persistent mapping)
            New-PSDrive -Name $driveLetter.TrimEnd(':') -PSProvider FileSystem -Root $networkPath -Persist -Scope Global -ErrorAction Stop
            Write-Host "Successfully mapped $driveLetter to $networkPath" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Failed to map $driveLetter to $networkPath : $_" -ForegroundColor Red
    }
}

Write-Host "`nDrive mapping complete!" -ForegroundColor Cyan
