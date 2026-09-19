@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Lenovo network and platform drivers
set "DRIVERDIR=%~dp0$WinPEDriver$"
set "DRIVERLOG=%SystemRoot%\Temp\Lenovo-bootstrap-drivers.log"
if not exist "%DRIVERDIR%" (
  echo Driver folder missing. Run this file from the installation USB.
  pause
  exit /b 2
)
echo Run this command as administrator, or from the Windows setup command prompt.
echo Windows will install signed drivers that match the detected hardware.
echo A log will be saved to %DRIVERLOG%
echo.
pnputil.exe /add-driver "%DRIVERDIR%\*.inf" /subdirs /install >"%DRIVERLOG%" 2>&1
set "DRIVERRESULT=%ERRORLEVEL%"
type "%DRIVERLOG%"
pnputil.exe /scan-devices
echo.
echo Driver staging finished with code %DRIVERRESULT%.
echo If a network adapter still does not appear, restart Windows and check again.
echo Once connected, run Windows Update and Lenovo System Update for remaining
echo graphics, audio and other model-specific updates.
echo No restart will be performed automatically.
pause
exit /b %DRIVERRESULT%
