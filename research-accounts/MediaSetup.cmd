@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Windows 11 installation - account choice

rem wpeinit.exe is invoked by winpeshl.ini before this script.
rem Profiles and the marker live on the physical installation media.
set "MSW11_MEDIA="
set "MSW11_DUPLICATE="
for %%D in (C D E F G H I J K L M N O P Q R S T U V W Y Z) do call :FindMedia %%D:
if defined MSW11_DUPLICATE goto AmbiguousMedia
if not defined MSW11_MEDIA goto MissingMedia
if not exist "%MSW11_MEDIA%\profiles\local.xml" goto IncompleteMedia
if not exist "%MSW11_MEDIA%\profiles\microsoft.xml" goto IncompleteMedia
if not exist "%MSW11_MEDIA%\sources\setup.exe" goto IncompleteMedia

:AccountMenu
cls
echo Windows 11 installation
echo.
echo Choose the account you want to create during setup:
echo.
echo   [1] Local account - choose your own name and password on this PC
echo   [2] Microsoft account - sign in online during setup
echo   [3] Command prompt for troubleshooting
echo   [4] Shut down
echo.
echo You will choose the installation disk in Windows Setup.
echo.
rem Delayed expansion substitutes typed text after CMD recognizes operators.
rem Never use CALL, percent expansion, or execution on the entered text.
setlocal EnableDelayedExpansion
set "MSW11_SELECTION="
set /p "MSW11_SELECTION=Type 1, 2, 3 or 4, then press Enter: "
if "!MSW11_SELECTION!"=="1" (
    endlocal
    goto LocalAccount
)
if "!MSW11_SELECTION!"=="2" (
    endlocal
    goto MicrosoftAccount
)
if "!MSW11_SELECTION!"=="3" (
    endlocal
    goto Troubleshoot
)
if "!MSW11_SELECTION!"=="4" (
    endlocal
    goto Shutdown
)
endlocal
goto AccountMenu

:LocalAccount
set "MSW11_PROFILE=local"
cls
echo Local account selected.
echo.
echo Disconnect Ethernet and leave Wi-Fi disconnected until the desktop.
echo Windows Setup will ask you for your account name and password.
echo You can connect to the internet after reaching the desktop.
echo.
pause
goto StartSetup

:MicrosoftAccount
set "MSW11_PROFILE=microsoft"
cls
echo Microsoft account selected.
echo.
echo Connect Ethernet now, or choose Wi-Fi when Windows asks.
echo Sign in to your Microsoft account during setup.
echo.
pause

:StartSetup
echo Starting Windows Setup...
start "" /wait "%MSW11_MEDIA%\sources\setup.exe" /unattend:"%MSW11_MEDIA%\profiles\%MSW11_PROFILE%.xml"
set "MSW11_RESULT=%ERRORLEVEL%"
echo.
echo Windows Setup exited with code %MSW11_RESULT%.
echo If installation has finished copying files, remove the USB drive
echo before restarting so the computer starts its new Windows installation.
echo.
echo Restart before choosing a different account installation profile.
echo Enter EXIT in the troubleshooting prompt to restart.
cmd.exe /d
wpeutil.exe reboot
exit /b

:Troubleshoot
echo Installation media: %MSW11_MEDIA%
echo Optional E485 helper: "%MSW11_MEDIA%\Enable-E485-Compatibility.cmd"
echo Enter EXIT to return to the account menu.
cmd.exe /d
goto AccountMenu

:Shutdown
wpeutil.exe shutdown
exit /b

:FindMedia
if not exist "%~1\MSW11-MEDIA.ID" exit /b
rem Read the first marker line with CMD built-ins only.
rem The drive argument comes only from the fixed list in the caller.
setlocal EnableDelayedExpansion
set "MSW11_MARKER="
set /p "MSW11_MARKER="<"%~1\MSW11-MEDIA.ID"
if "!MSW11_MARKER!"=="MSW11-LENOVO-2026-09-18" (
    endlocal
    if defined MSW11_MEDIA set "MSW11_DUPLICATE=1"
    set "MSW11_MEDIA=%~1"
    exit /b
)
endlocal
exit /b

:AmbiguousMedia
echo More than one matching installation drive is connected.
echo Disconnect the extra copy and restart the computer.
goto RecoveryPrompt

:MissingMedia
echo The matching Windows installation drive could not be found.
echo Check that the USB drive is connected, then restart the computer.
goto RecoveryPrompt

:IncompleteMedia
echo The installation drive is missing a required setup file or profile.
echo Review the media contents before installing Windows.

:RecoveryPrompt
echo.
echo Enter EXIT in the troubleshooting prompt to restart.
cmd.exe /d
wpeutil.exe reboot
exit /b
