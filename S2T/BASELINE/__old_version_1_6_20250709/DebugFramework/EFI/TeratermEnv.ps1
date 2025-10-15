param(
    [string]$ip,
    [string]$com
)

# Define the environment variables and their desired values
$initHostVariables = @{
    'FrameworkSerial' = $com
    'FrameworkIPAdress' = $ip
    'FrameworkDefaultPass' = 'root'
    'FrameworkDefaultUser' = 'password'
}

function CheckAndUpdateEnvVariables($variables) {
    foreach ($varName in $variables.Keys) {
        $desiredValue = $variables[$varName]
        $currentValue = [System.Environment]::GetEnvironmentVariable($varName, [System.EnvironmentVariableTarget]::User)

        if ($null -eq $currentValue) {
            # Environment variable does not exist, create it
            [System.Environment]::SetEnvironmentVariable($varName, $desiredValue, [System.EnvironmentVariableTarget]::User)
            Write-Host "Created environment variable '$varName' with value '$desiredValue'."
        } elseif ($currentValue -ne $desiredValue) {
            # Environment variable exists but has a different value, update it
            [System.Environment]::SetEnvironmentVariable($varName, $desiredValue, [System.EnvironmentVariableTarget]::User)
            Write-Host "Updated environment variable '$varName' from '$currentValue' to '$desiredValue'."
        } else {
            # Environment variable exists and has the correct value
            Write-Host "Environment variable '$varName' already exists with the correct value '$currentValue'."
        }
    }
}

# Check and update environment variables
CheckAndUpdateEnvVariables -variables $initHostVariables