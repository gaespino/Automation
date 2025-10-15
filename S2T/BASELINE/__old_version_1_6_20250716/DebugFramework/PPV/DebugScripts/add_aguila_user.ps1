#Requires -RunAsAdministrator
$defaultCookie = if (Test-Path C:\Windows\System32\config\systemprofile\.erlang.cookie)
{ 
    Get-Content C:\Windows\System32\config\systemprofile\.erlang.cookie -First 1
}else{
    Write-Host "Could not find erlang.cookie in default location" 
    exit 1
}

$userCookie = if (Test-Path $home\.erlang.cookie){ Get-Content $home\.erlang.cookie -First 1}else{"none"}
Write-Host $userCookie
if ($userCookie -ne $defaultCookie)
{
    Write-Host "updating users cookie value" 
    if (Test-Path $home\.erlang.cookie){Get-Item -Path "$home\.erlang.cookie" | Set-ItemProperty -Name IsReadOnly -Value $false -Force}
    Copy-Item -Path "C:\Windows\System32\config\systemprofile\.erlang.cookie" -Destination "$home\.erlang.cookie" -Force
}
else
{
    Write-Host "Users cookie value is good to go"   
}

$rabbitPath = Resolve-Path "C:\Program Files\RabbitMQ Server\rabbitmq_server*\sbin"
Write-Host $rabbitPath
if($rabbitPath){
    #make sure services is running
    $ServiceName = 'RabbitMQ'
    $rabbitService = Get-Service -Name $ServiceName

    while ($rabbitService.Status -ne 'Running')
    {
        Start-Service $ServiceName
        write-host $rabbitService.status
        write-host 'Service starting'
        Start-Sleep -seconds 5
        $rabbitService.Refresh()
    }
    if ($rabbitService.Status -eq 'Running')
    {
        Write-Host 'Service is now Running'
    }
}
else {
    Write-Host "Could not find path to RabbitMQ Server CLI files"
    exit 1 
}

cd $rabbitPath
$users = cmd.exe /c "rabbitmqctl list_users"
Write-Host $users
if ($users -like "*aguila*"){
    write-host "aguila user exists"
}
else{
    Write-Host "creating user"
    cmd.exe /c "rabbitmqctl.bat add_user aguila aguila"
    cmd.exe /c "rabbitmqctl.bat set_permissions -p / aguila .* .* .*"
}
cmd.exe /c "rabbitmqctl list_permissions"