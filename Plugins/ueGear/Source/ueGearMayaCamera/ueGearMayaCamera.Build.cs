using UnrealBuildTool;

public class ueGearMayaCamera : ModuleRules
{
    public ueGearMayaCamera(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
                // ... add public include paths required here ...
            }
        );
				
		
        PrivateIncludePaths.AddRange(
            new string[] {
                // ... add other private include paths required here ...
            }
        );
			
		
        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
				
                "MovieScene",
                "MovieSceneTools",
                "MovieSceneTracks",
            }
        );
			
		
        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "Projects",
                "InputCore",
                "EditorFramework",
                "UnrealEd",
                "ToolMenus",
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore", 
                "FBX",
                "CinematicCamera",
                "Sequencer",
                "MovieSceneTracks",
				
            }
        );
		
		
        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
                // ... add any modules that your module loads dynamically here ...
            }
        );
    }
}