#include "SkeletalMeshWeightTools.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

#define LOCTEXT_NAMESPACE "SkeletalMeshWeightTools"

bool USkeletalMeshWeightTools::ExportSkinWeights(USkeletalMesh* SkeletalMesh, const FString& SavePath)
{
    if (!SkeletalMesh || !SkeletalMesh->GetImportedModel())
    {
        UE_LOG(LogTemp, Warning, TEXT("Invalid SkeletalMesh"));
        return false;
    }

    FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
    FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0]; // LOD0

    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> VerticesArray;

    for (const FSkelMeshSection& Section : LODModel.Sections)
    {
        for (const FSoftSkinVertex& Vertex : Section.SoftVertices)
        {
            TSharedPtr<FJsonObject> VtxObj = MakeShared<FJsonObject>();
            TArray<TSharedPtr<FJsonValue>> Influences;

            for (int i = 0; i < MAX_TOTAL_INFLUENCES; i++)
            {
                if (Vertex.InfluenceWeights[i] > 0)
                {
                    TSharedPtr<FJsonObject> InfObj = MakeShared<FJsonObject>();
                    InfObj->SetNumberField(TEXT("BoneIndex"), Vertex.InfluenceBones[i]);
                    InfObj->SetNumberField(TEXT("Weight"), Vertex.InfluenceWeights[i] / 255.f);
                    Influences.Add(MakeShared<FJsonValueObject>(InfObj));
                }
            }

            VtxObj->SetArrayField(TEXT("Influences"), Influences);
            VerticesArray.Add(MakeShared<FJsonValueObject>(VtxObj));
        }
    }

    Root->SetArrayField(TEXT("Vertices"), VerticesArray);

    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(Root, Writer);

    return FFileHelper::SaveStringToFile(OutputString, *SavePath);
}

bool USkeletalMeshWeightTools::ImportSkinWeights(USkeletalMesh* SkeletalMesh, const FString& LoadPath)
{
    if (!SkeletalMesh || !SkeletalMesh->GetImportedModel())
    {
        UE_LOG(LogTemp, Warning, TEXT("Invalid SkeletalMesh"));
        return false;
    }

    FString FileContents;
    if (!FFileHelper::LoadFileToString(FileContents, *LoadPath))
    {
        UE_LOG(LogTemp, Warning, TEXT("Could not load file %s"), *LoadPath);
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(FileContents);

    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to parse JSON"));
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* VerticesArray;
    if (!Root->TryGetArrayField(TEXT("Vertices"), VerticesArray))
    {
        UE_LOG(LogTemp, Warning, TEXT("No Vertices field in JSON"));
        return false;
    }

    FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
    FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0];

    int32 VtxIndex = 0;
    for (FSkelMeshSection& Section : LODModel.Sections)
    {
        for (FSoftSkinVertex& Vertex : Section.SoftVertices)
        {
            if (VtxIndex >= VerticesArray->Num()) break;

            const TSharedPtr<FJsonObject>& VtxObj = (*VerticesArray)[VtxIndex++]->AsObject();
            const TArray<TSharedPtr<FJsonValue>>* InfluencesArray;

            if (VtxObj->TryGetArrayField(TEXT("Influences"), InfluencesArray))
            {
                FMemory::Memset(Vertex.InfluenceBones, 0, sizeof(Vertex.InfluenceBones));
                FMemory::Memset(Vertex.InfluenceWeights, 0, sizeof(Vertex.InfluenceWeights));

                int InfIdx = 0;
                for (const TSharedPtr<FJsonValue>& InfVal : *InfluencesArray)
                {
                    if (InfIdx >= MAX_TOTAL_INFLUENCES) break;

                    const TSharedPtr<FJsonObject> InfObj = InfVal->AsObject();
                    int32 BoneIdx = InfObj->GetIntegerField(TEXT("BoneIndex"));
                    float Weight = InfObj->GetNumberField(TEXT("Weight"));

                    Vertex.InfluenceBones[InfIdx] = (uint8)BoneIdx;
                    Vertex.InfluenceWeights[InfIdx] = (uint8)(Weight * 255.f);
                    InfIdx++;
                }
            }
        }
    }

    // Mark mesh dirty so UE saves & recompiles
    SkeletalMesh->MarkPackageDirty();
    SkeletalMesh->PostEditChange();

    return true;
}

#undef LOCTEXT_NAMESPACE
