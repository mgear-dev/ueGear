import unreal


@unreal.uclass()
class UeGearCommands(unreal.BlueprintFunctionLibrary):

    @unreal.ufunction(static=True)
    def hello_uegear():
        unreal.log('Hello ueGear')
