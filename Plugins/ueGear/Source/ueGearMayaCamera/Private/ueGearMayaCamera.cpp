#include "ueGearMayaCamera.h"
#include "GearMayaTrackEditor.h"
#include "Modules/ModuleManager.h"
#include "ISequencerModule.h"

IMPLEMENT_MODULE(FueGearMayaCameraModule, ueGearMayaCamera)

void FueGearMayaCameraModule::StartupModule()
{
	// Register with the sequencer module
	ISequencerModule& SequencerModule = FModuleManager::Get().LoadModuleChecked<ISequencerModule>("Sequencer");
	GearMayaTrackEditorHandle = SequencerModule.RegisterTrackEditor(FOnCreateTrackEditor::CreateStatic(&GearMayaTrackEditor::CreateTrackEditor));
}

void FueGearMayaCameraModule::ShutdownModule()
{
	// Unregister sequencer track creation delegates
	ISequencerModule* SequencerModule = FModuleManager::GetModulePtr<ISequencerModule>( "Sequencer" );
	if ( SequencerModule != nullptr )
	{
		SequencerModule->UnRegisterTrackEditor( GearMayaTrackEditorHandle );
	}
}


    
