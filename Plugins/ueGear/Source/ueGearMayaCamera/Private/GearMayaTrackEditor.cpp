#include "GearMayaTrackEditor.h"

#include "IMovieSceneBoundObjectProxy.h"
#include "MeshAttributeArray.h"
#include "Tracks/MovieScenePropertyTrack.h"
#include <unordered_map>

#include "Sections/MovieSceneFloatSection.h"
#include "Tracks/MovieSceneFloatTrack.h"


#define INCH_TO_MM(value) (value * 25.4)


bool GearMayaTrackEditor::ImportAnimatedProperty(const FString& InPropertyName, const FRichCurve& InCurve, FGuid InBinding, UMovieScene* InMovieScene)
{
	// check whether this property is something we can import
	if (InPropertyName != "FilmWidth" && 
		InPropertyName != "FilmHeight" )
	{
		return false;
	}

	// Maya to Unreal attribute lookup
	// These are the attributes that if found on fbx import camera will have there animation
	// applied to the specified unreal attribute
	TMap<FString, FString> MayaToUnrealLookup;
	MayaToUnrealLookup.Add(TEXT("FilmWidth"), TEXT("Filmback.SensorWidth"));
	MayaToUnrealLookup.Add(TEXT("FilmHeight"), TEXT("Filmback.SensorHeight"));
	
	FMovieSceneBinding* movieSceneBinding = InMovieScene->FindBinding(InBinding);
	FMovieScenePossessable* possesed = InMovieScene->FindPossessable(InBinding);

	// Finds the CameraComponent, by looking for Possessable tracks and comparing the guid to the camera.
	for (int i=0; i<InMovieScene->GetPossessableCount(); i+=1)
	{
		FMovieScenePossessable possessableTrack = InMovieScene->GetPossessable(i);
		if (possessableTrack.GetParent() == InBinding)
		{
			UE_LOG(LogTemp, Log, TEXT("Camera bound possessed found %s"), *possessableTrack.GetName() );

			FMovieSceneBinding* CameraComponentBinding = InMovieScene->FindBinding(possessableTrack.GetGuid());
			if (CameraComponentBinding)
			{
				for (auto CameraComponentTrack : CameraComponentBinding->GetTracks())
				{
					UE_LOG(LogTemp, Log, TEXT("   CameraComponent Track %s"), *CameraComponentTrack->GetDisplayName().ToString());
				}

				// Checks if name animated track exists, else creates it

				UMovieSceneFloatTrack* sensorTrack = InMovieScene->FindTrack<UMovieSceneFloatTrack>(possessableTrack.GetGuid(), *MayaToUnrealLookup[InPropertyName]);

				if (!sensorTrack)
				{
					InMovieScene->Modify();

					// Adds the track
					UMovieSceneFloatTrack* newSensorTrack = InMovieScene->AddTrack<UMovieSceneFloatTrack>(possessableTrack.GetGuid());

					// Sets up the relation between the track and the camera property
					newSensorTrack->SetPropertyNameAndPath(*MayaToUnrealLookup[InPropertyName], MayaToUnrealLookup[InPropertyName]);

					// todo: Create Section for fcurve data

					UMovieSceneFloatSection* TakeSection = nullptr;
					if (newSensorTrack->GetAllSections().Num() == 0)
					{
						TakeSection = Cast<UMovieSceneFloatSection>(newSensorTrack->CreateNewSection());
						newSensorTrack->Modify();
						newSensorTrack->AddSection(*TakeSection);
					}
					else
					{
						TakeSection = Cast<UMovieSceneFloatSection>(newSensorTrack->GetAllSections()[0]);
					}
					check(TakeSection);

					// Read FCurve data
					FFrameRate FrameRate = InMovieScene->GetTickResolution();
					TArray<FFrameNumber> KeyTimes;
					TArray<FMovieSceneFloatValue> KeyFloatValues;
					for (TArray<FKeyHandle>::TConstIterator KeyHandle = InCurve.GetKeyHandleIterator(); KeyHandle; ++KeyHandle)
					{
						const FRichCurveKey &Key = InCurve.GetKey(*KeyHandle);
						FFrameNumber KeyTime = (Key.Time * FrameRate).RoundToFrame();
						FMovieSceneFloatValue KeyValue(INCH_TO_MM(Key.Value));
						KeyTimes.Add(KeyTime);
						KeyFloatValues.Add(KeyValue);
					}

					TakeSection->Modify();
					
					// Apply Read FCurve data onto Take
					FMovieSceneFloatChannel* FloatChannel = &TakeSection->GetChannel();
					FloatChannel->Set(KeyTimes, KeyFloatValues);
					FloatChannel->SetKeysOnly(KeyTimes, KeyFloatValues);
					TakeSection->Modify();
					
					// Resize the Clip to fit the animated curve data
					TOptional<TRange<FFrameNumber>> AutoSizeRange = TakeSection->GetAutoSizeRange();
					if (AutoSizeRange.IsSet())
					{
						TakeSection->SetRange(AutoSizeRange.GetValue());
					}
					
				}
			}
		}
	}
	
	return true;
}


bool GearMayaTrackEditor::ImportStringProperty(const FString& InPropertyName, const FString& InStringValue, FGuid InBinding, UMovieScene* InMovieScene)
{
	return false;
}

bool GearMayaTrackEditor::SupportsType(TSubclassOf<UMovieSceneTrack> Type) const
{
	return true;
}


TSharedRef<ISequencerTrackEditor> GearMayaTrackEditor::CreateTrackEditor( TSharedRef<ISequencer> InSequencer )
{
	return MakeShareable( new GearMayaTrackEditor( InSequencer ) );
}