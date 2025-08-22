// Copyright 2022, ueGear Dev Team, All rights reserved

#pragma once

#include "CoreMinimal.h"
#include "UeGearCommands.generated.h"


UCLASS(Blueprintable)
class UEGEAR_API UUeGearCommands : public UObject
{
	GENERATED_BODY()
	
public:
	UFUNCTION(BlueprintCallable, Category=ueGear)
	static UUeGearCommands* Get();
};