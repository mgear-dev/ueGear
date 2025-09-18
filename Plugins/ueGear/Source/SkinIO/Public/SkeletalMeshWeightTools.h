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

	UFUNCTION(CallInEditor, BlueprintCallable, Category="SkeletalMesh Weights")
	static bool GetSubMeshNames(USkeletalMesh* SkeletalMesh);

private:
		
	static TMap<FString, TMap<int32, float >> GenerateWeightDictionary(USkeletalMesh* SkeletalMesh);

	static TArray<FVector3f> GetVertices(USkeletalMesh* SkeletalMesh);
};
