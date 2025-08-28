@echo off
setlocal EnableDelayedExpansion

REM The following builds the plugin for
REM - Unreal 5.4
REM - Unreal 5.5
REM - Unreal 5.6

REM Escape character for ANSI codes
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

REM Check the operating system
if "%OS%"=="Windows_NT" (
    echo Running on Windows

    REM Get the current directory
    set "rootPath=%CD%"
    echo Current directory is: !rootPath!

    REM Build 5.2
    if exist "C:\Program Files\Epic Games\UE_5.2" (
        call "C:\Program Files\Epic Games\UE_5.2\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.0.3_UE5.2\ueGear" -Rocket -VS2019 || echo Failed to find Unreal 5.2
    )

    REM Build 5.3
    if exist "C:\Program Files\Epic Games\UE_5.3" (
        echo %ESC%[32m=== 5.3 ===%ESC%[0m
        call "C:\Program Files\Epic Games\UE_5.3\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.0.3_UE5.3\ueGear" -Rocket -VS2022 || echo Failed to find Unreal 5.3
    )

    REM Build 5.4
    if exist "C:\Program Files\Epic Games\UE_5.4" (
        echo %ESC%[32m=== 5.4 ===%ESC%[0m
        call "C:\Program Files\Epic Games\UE_5.4\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.0.3_UE5.4\ueGear" -Rocket -VS2022 || echo Failed to find Unreal 5.4
    )

    REM Build 5.5
    if exist "C:\Program Files\Epic Games\UE_5.5" (
        echo %ESC%[32m=== 5.5 ===%ESC%[0m
        call "C:\Program Files\Epic Games\UE_5.5\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.0.3_UE5.5\ueGear" -Rocket -VS2022 || echo Failed to find Unreal 5.5
    )

    REM Build 5.6
    if exist "C:\Program Files\Epic Games\UE_5.6" (
        echo %ESC%[32m=== 5.6 ===%ESC%[0m
        call "C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="!rootPath!\Plugins\ueGear\ueGear.uplugin" -Package="!rootPath!\Package\ueGear_1.0.3_UE5.6\ueGear" -Rocket -VS2022 || echo Failed to find Unreal 5.6
    )

) else (
    echo This script is designed for Windows only.
)

endlocal
pause
