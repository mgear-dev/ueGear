
#!/bin/bash

# The following builds the plugin for 
# - Unreal 5.2
# - Unreal 5.3

# Check the operating system
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    echo "Running on macOS"
    # Get the current directory
    rootPath=$(pwd)

    echo "  Current directory is: ${rootPath}"

    # Call the Unreal Engine UAT script for macOS

    # Build 5.2
    if [ -e "/Users/Shared/Epic Games/UE_5.2" ]; then
        '/Users/Shared/Epic Games/UE_5.2/Engine/Build/BatchFiles/RunUAT.sh' BuildPlugin -Plugin="${rootPath}/Plugins/ueGear/ueGear.uplugin" -Package="${rootPath}/Package/ueGear_5.2" -architecture=arm64 || echo "Failed to find Unreal 5.2"
    fi

    # Build 5.3
    if [ -e "/Users/Shared/Epic Games/UE_5.3" ]; then
        '/Users/Shared/Epic Games/UE_5.3/Engine/Build/BatchFiles/RunUAT.sh' BuildPlugin -Plugin="${rootPath}/Plugins/ueGear/ueGear.uplugin" -Package="${rootPath}/Package/ueGear_5.3" -architecture=arm64 || echo "Failed to find Unreal 5.3"
    fi

elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # Linux
    echo "Running on Linux"
    # Call the Unreal Engine UAT script for Linux
    /path/to/UnrealEngine/Engine/Build/BatchFiles/RunUAT.sh MyUATCommand

# elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" -o "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
#     # Windows
#     echo "Running on Windows"
#     # Call the Unreal Engine UAT script for Windows
#     "C:\Program Files\Epic Games\UE_5.2\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="%rootPath%\Plugins\ueGear\ueGear.uplugin" -Package="%rootPath%\Package\ueGear_5.2" -Rocket -VS2019
#     "C:\Program Files\Epic Games\UE_5.3\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin -Plugin="%rootPath%\Plugins\ueGear\ueGear.uplugin" -Package="%rootPath%\Package\ueGear_5.3" -Rocket -VS2019

else
    echo "Unsupported operating system"
    exit 1
fi




