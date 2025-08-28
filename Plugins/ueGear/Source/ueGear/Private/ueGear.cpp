// Copyright 2022, ueGear Dev Team, All rights reserved

#include "ueGear.h"

#include "LevelEditor.h"
#include "UeGearCommands.h"

#define LOCTEXT_NAMESPACE "FueGearModule"

DEFINE_LOG_CATEGORY(ueGearLog)

void FueGearModule::StartupModule()
{
	UE_LOG(ueGearLog, Log, TEXT("Creating ueGear Menus"));
	FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule> ("LevelEditor");
	TSharedPtr<FExtender> MenuExtender = MakeShareable(new FExtender());
	MenuExtender->AddMenuBarExtension(
		"Help",
		EExtensionHook::Before,
		nullptr,
		FMenuBarExtensionDelegate::CreateRaw(this, &FueGearModule::AddMenuEntry));
	LevelEditorModule.GetMenuExtensibilityManager()->AddExtender(MenuExtender);
}

void FueGearModule::ShutdownModule()
{
	IModuleInterface::ShutdownModule();
}

void FueGearModule::AddMenuEntry(FMenuBarBuilder& MenuBarBuilder)
{
	MenuBarBuilder.AddPullDownMenu(
		LOCTEXT("MenuLocKey", "ueGear"),
		LOCTEXT("MenuTooltipKey", "Opens ueGear Menu"),
		FNewMenuDelegate::CreateRaw(this, &FueGearModule::FillMenu),
		FName(TEXT("ueGear")),
		FName(TEXT("ueGear")));
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