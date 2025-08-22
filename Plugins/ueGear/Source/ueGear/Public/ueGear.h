// Copyright 2022, ueGear Dev Team, All rights reserved

#pragma once

#include "CoreMinimal.h"

DECLARE_LOG_CATEGORY_EXTERN(ueGearLog, Log, All);

class FueGearModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	
	void AddMenuEntry(FMenuBarBuilder& MenuBarBuilder);
	void FillMenu(FMenuBuilder& MenuBuilder);
	
	void GenerateUegearUiCallback();
};