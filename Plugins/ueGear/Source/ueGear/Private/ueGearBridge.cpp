// Fill out your copyright notice in the Description page of Project Settings.


#include "ueGearBridge.h"

UueGearBridge* UueGearBridge::Get()
{
	TArray<UClass*> ueGearBridgeClasses;
	GetDerivedClasses(UueGearBridge::StaticClass(), ueGearBridgeClasses);
	int32 NumClasses = ueGearBridgeClasses.Num();
	if (NumClasses > 0)
	{
		return Cast<UueGearBridge>(ueGearBridgeClasses[NumClasses - 1]->GetDefaultObject());
	}
	return nullptr;
}
