// Copyright 2022, ueGear Dev Team, All rights reserved

#include "ueGear.h"

#include "LevelEditor.h"
#include "ToolMenus.h"
#include "UeGearCommands.h"

#define LOCTEXT_NAMESPACE "FueGearModule"

DEFINE_LOG_CATEGORY(ueGearLog)

void FueGearModule::StartupModule()
{
	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FueGearModule::RegisterMenu));
}

void FueGearModule::ShutdownModule()
{
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);
}

void FueGearModule::RegisterMenu()
{
	UE_LOG(ueGearLog, Log, TEXT("Creating ueGear Menus"));

	FToolMenuOwnerScoped OwnerScoped(this);
	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
		FToolMenuSection& Section = Menu->FindOrAddSection("Rigging", LOCTEXT("MenuSectKey", "Rigging"));
		Section.AddSubMenu(
			FName(TEXT("ueGear")),
			LOCTEXT("MenuLocKey", "ueGear"),
			LOCTEXT("MenuTooltipKey", "Opens ueGear Menu"),
			FNewMenuDelegate::CreateRaw(this, &FueGearModule::FillMenu),
			false,
			FSlateIcon(),
			false,
			FName(TEXT("ueGear")));
	}
}

void FueGearModule::FillMenu(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.AddMenuEntry(
		FText::FromString("Generate ueGear Rig"),
		FText::FromString("Generates a ueGear Control Rig from an mGear context."),
		FSlateIcon(),
		FUIAction(FExecuteAction::CreateRaw(this, &FueGearModule::GenerateUegearUiCallback))
	);
}

void FueGearModule::GenerateUegearUiCallback()
{
	UUeGearCommands* ueGearCommands = UUeGearCommands::Get();
	ueGearCommands->GenerateUegearUi();
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FueGearModule, ueGear)
