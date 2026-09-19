$ErrorActionPreference = 'Stop'
$logVolume = Get-Volume -FileSystemLabel 'T15GLOGS'
$dest = "$($logVolume.DriveLetter):\"
Start-Transcript -Path ($dest + 'transcript.txt') -Force
$before = Get-WindowsDriver -Online
$before | Select-Object Driver,OriginalFileName,ProviderName,ClassName,Date,Version | ConvertTo-Json -Depth 3 | Set-Content ($dest + 'before-drivers.json')
$secureBoot = Confirm-SecureBootUEFI
$user = Get-LocalUser MediaTest | Select-Object Name,Enabled,PrincipalSource
$arguments = @('/add-driver', "$PSScriptRoot\Drivers\*.inf", '/subdirs')
& pnputil.exe @arguments 2>&1 | Tee-Object -FilePath ($dest + 'pnputil-add-driver.txt')
$code = $LASTEXITCODE
$after = Get-WindowsDriver -Online
$after | Select-Object Driver,OriginalFileName,ProviderName,ClassName,Date,Version | ConvertTo-Json -Depth 3 | Set-Content ($dest + 'after-drivers.json')
@{SecureBoot=$secureBoot;User=$user;PnpUtilExitCode=$code;BeforeThirdPartyDriverCount=$before.Count;AfterThirdPartyDriverCount=$after.Count;RunAt=(Get-Date).ToString('o');Command='pnputil.exe /add-driver <input>\Drivers\*.inf /subdirs';InstallFlagUsed=$false;NetworkAdapterPresent=$false} | ConvertTo-Json -Depth 5 | Set-Content ($dest + 'result.json')
Copy-Item "$env:windir\INF\setupapi.dev.log" ($dest + 'setupapi.dev.log')
Copy-Item "$env:windir\INF\setupapi.app.log" ($dest + 'setupapi.app.log') -ErrorAction SilentlyContinue
Write-Host "T15G VALIDATION COMPLETE. Exit code: $code. Drivers before: $($before.Count); after: $($after.Count). Secure Boot: $secureBoot"
Stop-Transcript
