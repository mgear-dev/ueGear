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


    REM Build 5.5
    if exist "E:\UnrealEngines\UE_5.6" (
        call "E:\UnrealEngines\UE_5.6\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.1_UE5.6\ueGear" -Rocket -VS2022 || echo Failed to find Unreal 5.6
    )

) else (
    echo This script is designed for Windows only.
)

endlocal
pause
