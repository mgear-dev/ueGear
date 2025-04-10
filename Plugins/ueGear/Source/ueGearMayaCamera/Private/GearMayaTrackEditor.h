#pragma once

#include "IMovieSceneToolsTrackImporter.h"
#include "MovieSceneToolsModule.h"
#include "MovieSceneTrackEditor.h"

class GearMayaTrackEditor: public FMovieSceneTrackEditor, public IMovieSceneToolsTrackImporter
{
public:

	GearMayaTrackEditor(TSharedRef<ISequencer> InSequencer): FMovieSceneTrackEditor( InSequencer)
	{
		FMovieSceneToolsModule::Get().RegisterTrackImporter(this);
	}

	virtual ~GearMayaTrackEditor()
	{
		FMovieSceneToolsModule::Get().UnregisterTrackImporter(this);
	}

	static TSharedRef<ISequencerTrackEditor> CreateTrackEditor( TSharedRef<ISequencer> OwningSequencer );
	
public:
	// ISequencerTrackEditor interface
	virtual bool SupportsType( TSubclassOf<UMovieSceneTrack> Type ) const override;
	
	// IMovieSceneToolsTrackImporter
	virtual bool ImportAnimatedProperty(const FString& InPropertyName, const FRichCurve& InCurve, FGuid InBinding, UMovieScene* InMovieScene) override;
	virtual bool ImportStringProperty(const FString& InPropertyName, const FString& InStringValue, FGuid InBinding, UMovieScene* InMovieScene) override;
};
