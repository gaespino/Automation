param(
    [string]$ip,
    [string]$com,
    [string]$frameworkPass = "",
    [string]$dantaDbPass = ""
)

# SECURITY NOTE: Passwords are NOT hardcoded in this file to prevent Git credential leaks
# Passwords should be provided via parameters or will be read from existing environment variables
# If not available, user will be prompted to enter them securely

# Define the environment variables and their desired values
$initHostVariables = @{
    'FrameworkSerial' = $com
    'FrameworkIPAdress' = $ip
    'FrameworkDefaultPass' = $frameworkPass
    'FrameworkDefaultUser' = 'root'
    'DANTA_DB_PASSWORD' = $dantaDbPass
}

function CheckAndUpdateEnvVariables($variables) {
    foreach ($varName in $variables.Keys) {
        $desiredValue = $variables[$varName]
        $currentValue = [System.Environment]::GetEnvironmentVariable($varName, [System.EnvironmentVariableTarget]::User)

        # Special handling for password variables
        if ($varName -eq 'FrameworkDefaultPass' -or $varName -eq 'DANTA_DB_PASSWORD') {
            if ([string]::IsNullOrEmpty($desiredValue)) {
                # No password provided via parameter, check if already set
                if ($null -ne $currentValue -and -not [string]::IsNullOrEmpty($currentValue)) {
                    Write-Host "Password variable '$varName' already exists (keeping existing value)."
                    continue
                } else {
                    # Prompt user securely
                    Write-Host ""
                    Write-Host "SECURITY: Password for '$varName' not found." -ForegroundColor Yellow
                    Write-Host "Please enter the password (or press Enter to skip):" -ForegroundColor Yellow
                    $securePassword = Read-Host -AsSecureString
                    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
                    $desiredValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
                    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
                    
                    if ([string]::IsNullOrEmpty($desiredValue)) {
                        Write-Host "Skipped setting '$varName' (can be set manually later)." -ForegroundColor Gray
                        continue
                    }
                }
            }
        }

        if ($null -eq $currentValue) {
            # Environment variable does not exist, create it
            [System.Environment]::SetEnvironmentVariable($varName, $desiredValue, [System.EnvironmentVariableTarget]::User)
            if ($varName -eq 'FrameworkDefaultPass' -or $varName -eq 'DANTA_DB_PASSWORD') {
                Write-Host "Created environment variable '$varName' (password hidden for security)."
            } else {
                Write-Host "Created environment variable '$varName' with value '$desiredValue'."
            }
        } elseif ($currentValue -ne $desiredValue) {
            # Environment variable exists but has a different value, update it
            [System.Environment]::SetEnvironmentVariable($varName, $desiredValue, [System.EnvironmentVariableTarget]::User)
            if ($varName -eq 'FrameworkDefaultPass' -or $varName -eq 'DANTA_DB_PASSWORD') {
                Write-Host "Updated environment variable '$varName' (password hidden for security)."
            } else {
                Write-Host "Updated environment variable '$varName' from '$currentValue' to '$desiredValue'."
            }
        } else {
            # Environment variable exists and has the correct value
            if ($varName -eq 'FrameworkDefaultPass' -or $varName -eq 'DANTA_DB_PASSWORD') {
                Write-Host "Environment variable '$varName' already exists with correct value."
            } else {
                Write-Host "Environment variable '$varName' already exists with the correct value '$currentValue'."
            }
        }
    }
}

# Check and update environment variables
CheckAndUpdateEnvVariables -variables $initHostVariables

Write-Host ""
Write-Host "Environment variable setup complete."
Write-Host "Please restart PythonSV to load the new variables."
Write-Host ""
Write-Host "SECURITY NOTE: Passwords are NOT stored in Git." -ForegroundColor Cyan
Write-Host "For password values, contact your team lead or check internal documentation." -ForegroundColor Cyan
