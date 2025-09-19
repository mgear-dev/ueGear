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

    auto Weights = GenerateWeightDictionary(SkeletalMesh);
    auto Vertices = GetVertices(SkeletalMesh);
    
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> ObjDDic;
    TSharedRef<FJsonObject> ObjData = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> VerticesArray;
    TSharedRef<FJsonObject> WeightDataCollection = MakeShared<FJsonObject>();

    // Weights

    for (auto Weight : Weights)
    {
        TSharedRef<FJsonObject> WeightMeta = MakeShared<FJsonObject>();

        for (auto info : Weight.Value)
        {
            TSharedRef<FJsonObject> VertWeight = MakeShared<FJsonObject>();
            WeightMeta->SetNumberField( FString::FromInt(info.Key), info.Value);
        }
        
        WeightDataCollection->SetObjectField(Weight.Key, WeightMeta);
    }
    
    // Vertex
    
    for (int VertIdx = 0; VertIdx < Vertices.Num(); ++VertIdx)
    {
        TSharedPtr<FJsonObject> InfObj = MakeShared<FJsonObject>();
        InfObj->SetNumberField(TEXT("X"), Vertices[VertIdx].X);
        InfObj->SetNumberField(TEXT("Y"), Vertices[VertIdx].Y);
        InfObj->SetNumberField(TEXT("Z"), Vertices[VertIdx].Z);
        VerticesArray.Add(MakeShared<FJsonValueObject>(InfObj));
    }
    
    ObjData->SetNumberField(TEXT("vertexCount"), Vertices.Num());
    ObjData->SetObjectField("weights", WeightDataCollection);
    ObjData->SetArrayField(TEXT("vertices"), VerticesArray);
    ObjDDic.Add(MakeShared<FJsonValueObject>(ObjData));
    
    Root->SetArrayField(TEXT("objDDic"), ObjDDic);

    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(Root, Writer);

/* note: In the mGear Skin files. Each file represents 1 piece of Mesh.
 *  {"weights"} : {bone_name} : {vertex index : weight influence }
 *  - weight influence is between 0.0 > 1.0
 *
 *  note: Imported Geometry in Unreal can have its topoloogy changed by the importer
 *      - Vertex counts may not match
 *      - submeshes may be different
 */
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

// note: Not properly implemented -- most likely will be removed
bool USkeletalMeshWeightTools::GetSubMeshNames(USkeletalMesh* SkeletalMesh)
{
    if (!SkeletalMesh) return false;

    FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
    FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0];

    UE_LOG(LogTemp, Log, TEXT("LOD 0 has %d sections"), LODModel.Sections.Num());

    for (int32 SectionIndex = 0; SectionIndex <  LODModel.Sections.Num(); ++SectionIndex)
    {
        const FSkelMeshSection& Section = LODModel.Sections[SectionIndex];

        UE_LOG(LogTemp, Log, TEXT("  Section %d: MaterialIndex=%d, Vertices=%d, Bones=%d"),
            SectionIndex,
            Section.MaterialIndex,
            Section.NumVertices,
            Section.BoneMap.Num());
        
        UE_LOG(LogTemp, Log,TEXT("   Bone Influences %d"), Section.GetMaxBoneInfluences());

        // Print out the Bone's Name
        for (auto BoneIndex : Section.BoneMap)
        {
            FName BoneName = SkeletalMesh->GetRefSkeleton().GetRawRefBoneNames()[BoneIndex];
            UE_LOG(LogTemp, Log,TEXT("        Bone Names [%d] %s"), BoneIndex, *BoneName.ToString());
        }
    }
    
    auto InfluenceWeights = GenerateWeightDictionary(SkeletalMesh);
    for (auto InfluenceWeight : InfluenceWeights)
    {
        UE_LOG(LogTemp, Log,TEXT("Bone Name: %s"), *InfluenceWeight.Key);
        for (auto VertInfluence : InfluenceWeight.Value)
        {
            UE_LOG(LogTemp, Log,TEXT("    %d: %f"), VertInfluence.Key, VertInfluence.Value);
        }
    }

    TArray<FVector3f> VertexPositions = GetVertices(SkeletalMesh);
    for (int32 VertexIndex = 0; VertexIndex < VertexPositions.Num(); ++VertexIndex)
    {
        FVector3f Vertex = VertexPositions[VertexIndex];
        UE_LOG(LogTemp, Log, TEXT("    Vertex Position[%d]: %f, %f, %f"), VertexIndex, Vertex.X, Vertex.Y, Vertex.Z);
    }
    
    return true;
}

// todo: [x] Get Submeshes
// todo:    [x] Get Vertices positions
// todo:    [x] Get Vertices weights
// todo: [-] Compare Vertices           (ignored due to internat assets may be modified by import process)
// todo:    [-] compare size/count
// todo:    [-] compare order
// todo:    [-] compare positions
// todo: [-] Create a vertex checker, to see if vert count match and then if so assume its an unreal export.
// todo: [ ] Create 3D search structure [BVH] to quickly search positions and points close by.
// todo: [ ] Calculate Barycentric weight from closest points

/**
 * Generates the mGear wieght dictionary, structured to match the standard used in mGear.
 *
 * Layout:
 *      {Bone Name: { Vertex Index: Vertex Influence } }
 * - Vertex Index is stored as a string
 * - Vertex Influence is stored as a value between 0 and 1. if the value is 0 then the Vertex Index is ommitted. 
 */
TMap<FString, TMap<int32, float >> USkeletalMeshWeightTools::GenerateWeightDictionary(USkeletalMesh* SkeletalMesh)
{
    TMap<FString, TMap<int32, float>> JointWeights = TMap<FString, TMap<int32, float>>();

    if (!SkeletalMesh) return JointWeights;
    
    // Populate the Map with a list of all the joint names
    
    int32 NumberOfBones = SkeletalMesh->GetRefSkeleton().GetNum();
    for (int32 BoneIndex = 0; BoneIndex < NumberOfBones; ++BoneIndex)
    {
        auto BoneName = SkeletalMesh->GetRefSkeleton().GetBoneName(BoneIndex);
        JointWeights.Add(BoneName.ToString());
    }

    // Populate the Map's Value with vert and weight data
    
    FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
    FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0];
    
    for (int32 SectionIndex = 0; SectionIndex <  LODModel.Sections.Num(); ++SectionIndex)
    {
        const FSkelMeshSection& Section = LODModel.Sections[SectionIndex];
        {
            for (int VertIndex = 0; VertIndex < Section.SoftVertices.Num(); VertIndex++)
            {
                const FSoftSkinVertex& Vertex = Section.SoftVertices[VertIndex];
                TSharedPtr<FJsonObject> VtxObj = MakeShared<FJsonObject>();
                TArray<TSharedPtr<FJsonValue>> Influences;
                
                for (int i = 0; i < MAX_TOTAL_INFLUENCES; i++)
                {
                    if (Vertex.InfluenceWeights[i] > 0)
                    {
                        TSharedPtr<FJsonObject> InfObj = MakeShared<FJsonObject>();
                        // Converts the influence index for the vertex to the actual bone influnce index.
                        FBoneIndexType BoneIndex = Section.BoneMap[Vertex.InfluenceBones[i]];
                        float BoneInfluence =  Vertex.InfluenceWeights[i] / 255.f / 257.f;
                        auto BoneName = SkeletalMesh->GetRefSkeleton().GetRawRefBoneNames()[BoneIndex];
                        
                        JointWeights[BoneName.ToString()].Add(VertIndex, BoneInfluence);
                    }
                }
            }
        }
    }

    return JointWeights;
}

/**
 * Gets all the vertices in the order they appear in the LOD 0.
 * 
 * @param SkeletalMesh that will have all its LOD0 Vertices queried.
 * @return 
 */
TArray<FVector3f> USkeletalMeshWeightTools::GetVertices(USkeletalMesh* SkeletalMesh)
{
    TArray<FVector3f> Vertices;

    FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
    FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0];
    
    for (int32 SectionIndex = 0; SectionIndex <  LODModel.Sections.Num(); ++SectionIndex)
    {
        const FSkelMeshSection& Section = LODModel.Sections[SectionIndex];
        {
            for (int VertIndex = 0; VertIndex < Section.SoftVertices.Num(); VertIndex++)
            {
                const FSoftSkinVertex& Vertex = Section.SoftVertices[VertIndex];

                // UE_LOG(LogTemp, Log, TEXT("    Vertex Position[%d]: %f, %f, %f"),VertIndex, Vertex.Position.X, Vertex.Position.Y, Vertex.Position.Z);
                Vertices.Add(Vertex.Position);
            }
        }
    }
    return Vertices;
}

#undef LOCTEXT_NAMESPACE

// ------------------------------
//      Share the same index position.
// ------------------------------
// List of Vertex Position
// List of a1 object
//
// Index 
//
// a1 : {Bone Name : Bone Weight}