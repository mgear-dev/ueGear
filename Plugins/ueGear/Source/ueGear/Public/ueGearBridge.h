// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ueGearBridge.generated.h"

/**
 * 
 */
UCLASS(Blueprintable)
class UEGEAR_API UueGearBridge : public UObject
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = ueGear)
	static UueGearBridge* Get();

	UFUNCTION(BlueprintImplementableEvent, Category = ueGear)
	void HelloWorld() const;
};
