@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Optional Windows Setup compatibility checks

rem This must run only inside the USB installer's Windows PE session.
reg.exe query "HKLM\SYSTEM\CurrentControlSet\Control\MiniNT" >nul 2>&1
if errorlevel 1 goto NotWinPE

echo Applying the three booted-install compatibility settings used by Rufus.
echo These skip Setup's TPM, Secure Boot capability and RAM eligibility checks.
echo They do not switch off the computer's TPM or Secure Boot firmware settings.
echo They do not make an unsupported processor officially supported.
echo.

for %%V in (BypassTPMCheck BypassSecureBootCheck BypassRAMCheck) do (
    reg.exe add "HKLM\SYSTEM\Setup\LabConfig" /v %%V /t REG_DWORD /d 1 /f
    if errorlevel 1 goto Failed
)

echo.
echo The optional settings are active for this Windows PE session.
echo Close this prompt, return to Windows Setup, and retry the blocked step.
echo If the same block remains, inspect its exact message before proceeding.
echo These settings cannot supply CPU instructions missing from the processor.
echo.
pause
exit /b 0

:NotWinPE
echo This optional script must run from the USB installer's command prompt.
echo No settings were changed.
pause
exit /b 1

:Failed
echo.
echo A registry command failed. One or more settings may not have been applied.
echo Review the error above before continuing Windows Setup.
pause
exit /b 1
