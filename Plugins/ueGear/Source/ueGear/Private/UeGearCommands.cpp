// Copyright 2022, ueGear Dev Team, All rights reserved


#include "UeGearCommands.h"

UUeGearCommands* UUeGearCommands::Get()
{
	TArray<UClass*> UeGearCommandsClasses;
	GetDerivedClasses(UUeGearCommands::StaticClass(), UeGearCommandsClasses);
	int32 NumClasses = UeGearCommandsClasses.Num();
	if (NumClasses > 0)
	{
		return Cast<UUeGearCommands>(UeGearCommandsClasses[NumClasses - 1]->GetDefaultObject());
	}
	return nullptr;
}
