// Copyright Epic Games, Inc. All Rights Reserved.

#include "ueGear.h"

#define LOCTEXT_NAMESPACE "FueGearModule"

void FueGearModule::StartupModule()
{
	FString fs = FPaths::ConvertRelativePathToFull(FPaths::GetPath("../"));
	UE_LOG(LogTemp, Warning, TEXT("%s"), *fs);
}

void FueGearModule::ShutdownModule()
{
	FString fs = FPaths::GetPath("../");
	UE_LOG(LogTemp, Warning, TEXT("%s"), *fs);
	UE_LOG(LogTemp, Warning, TEXT("%s"), *FPaths::ConvertRelativePathToFull(fs));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FueGearModule, ueGear)