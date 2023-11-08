@echo off
setlocal EnableDelayedExpansion

REM The following builds the plugin for
REM - Unreal 5.2
REM - Unreal 5.3

REM Check the operating system
if "%OS%"=="Windows_NT" (
    echo Running on Windows

    REM Get the current directory
    set "rootPath=%CD%"
    echo Current directory is: !rootPath!

    REM Build 5.2
    if exist "C:\Program Files\Epic Games\UE_5.2" (
        call "C:\Program Files\Epic Games\UE_5.2\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_5.2" -Rocket -VS2019 || echo Failed to find Unreal 5.2
    )

    REM Build 5.3
    if exist "C:\Program Files\Epic Games\UE_5.3" (
        call "C:\Program Files\Epic Games\UE_5.3\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_5.3" -Rocket -VS2019 || echo Failed to find Unreal 5.3
    )
) else (
    echo This script is designed for Windows only.
)

endlocal
pause
