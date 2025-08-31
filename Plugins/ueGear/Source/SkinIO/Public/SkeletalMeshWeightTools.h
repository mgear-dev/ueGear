#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SkeletalMeshWeightTools.generated.h"

UCLASS()
class SKINIO_API USkeletalMeshWeightTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	/** Export vertex skin weights of SkeletalMesh to JSON file */
	UFUNCTION(CallInEditor, BlueprintCallable, Category="SkeletalMesh Weights")
	static bool ExportSkinWeights(USkeletalMesh* SkeletalMesh, const FString& SavePath);

	/** Import vertex skin weights from JSON file into SkeletalMesh */
	UFUNCTION(CallInEditor, BlueprintCallable, Category="SkeletalMesh Weights")
	static bool ImportSkinWeights(USkeletalMesh* SkeletalMesh, const FString& LoadPath);
};
