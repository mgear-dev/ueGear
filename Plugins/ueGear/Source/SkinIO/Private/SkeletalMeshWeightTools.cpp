#include "SkeletalMeshWeightTools.h"

#include "MeshDescriptionToDynamicMesh.h"
#include "RenderCore.h"
#include "SkinWeightModifier.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "Dom/JsonObject.h"
#include "DynamicMesh/DynamicMesh3.h"
#include "GeometryScript/MeshBoneWeightFunctions.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Operations/TransferBoneWeights.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "DynamicMesh/DynamicMesh3.h"
#include "DynamicMesh/DynamicMeshAttributeSet.h"

#define LOCTEXT_NAMESPACE "SkeletalMeshWeightTools"

/**
 * Exports the Skeletal Meshes weights and vertex position data into a json file.
 * 
 * @note In the mGear Skin files. Each file represents 1 piece of Mesh.
 *  {"weights"} : {bone_name} : {vertex index : weight influence }
 *  - weight influence is between 0.0 > 1.0
 *
 * @note Imported Geometry in Unreal can have its topoloogy changed by the importer
 *      - Vertex counts may not match
 *      - submeshes may be different
 */
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
    
    return FFileHelper::SaveStringToFile(OutputString, *SavePath);
}


void SetAllWeightsToRoot(USkeletalMesh* SkeletalMesh)
{
    if (!SkeletalMesh)
    {
        UE_LOG(LogTemp, Error, TEXT("SkeletalMesh is null."));
        return;
    }
 
    const FReferenceSkeleton& RefSkeleton = SkeletalMesh->GetRefSkeleton();
    if (RefSkeleton.GetNum() == 0)
    {
        UE_LOG(LogTemp, Error, TEXT("SkeletalMesh has no bones."));
        return;
    }
 
    USkinWeightModifier* Modifier = NewObject<USkinWeightModifier>();
    Modifier->SetSkeletalMesh(SkeletalMesh);
 
    FName FirstBoneName = RefSkeleton.GetBoneName(0);
    TMap<FName, float> Weights = {{ FirstBoneName, 1.0f }};
 
    int32 NumVertices = Modifier->GetNumVertices();
    for (int32 Index = 0; Index < NumVertices; ++Index)
    {
        Modifier->SetVertexWeights(Index, Weights, true);
    }
 
    if (Modifier->CommitWeightsToSkeletalMesh())
    {
        SkeletalMesh->MarkPackageDirty();
        SkeletalMesh->PostEditChange();
        UE_LOG(LogTemp, Log, TEXT("Weights updated to first bone successfully."));
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to commit skin weight changes."));
    }
}

// WIP:
// Extract Skeletal Mesh LOD to FDynamicMesh3 with skin weights attached
bool ExtractSkeletalMeshLODToDynamicMesh(const USkeletalMesh* SkeletalMesh, int32 LODIndex, UE::Geometry::FDynamicMesh3& OutMesh)
{
    FMeshDescription MeshDescription;
    SkeletalMesh->GetMeshDescription(LODIndex, MeshDescription);

    if (MeshDescription.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("No MeshDescription found on SkeletalMesh!"));
        return false;
    }

    // Register vertex/normals/UV attributes if not already
    FStaticMeshAttributes Attributes(MeshDescription);
    Attributes.Register();

    // Convert MeshDescription → DynamicMesh
    FMeshDescriptionToDynamicMesh Converter;
    Converter.Convert(&MeshDescription, OutMesh);
    
    return true;
}

// WIP: 
bool EditorTransferSkinWeightsBarycentric(USkeletalMesh* SourceSkeletalMesh, int32 SourceLODIndex, USkeletalMesh* TargetSkeletalMesh, int32 TargetLODIndex)
{
    // using namespace UE::Geometry;
 
    UE::Geometry::FDynamicMesh3 SourceDynamicMesh, TargetDynamicMesh;
    SourceDynamicMesh = UE::Geometry::FDynamicMesh3();
    TargetDynamicMesh = UE::Geometry::FDynamicMesh3();
    
    if (!ExtractSkeletalMeshLODToDynamicMesh(SourceSkeletalMesh, SourceLODIndex, SourceDynamicMesh)
        || !ExtractSkeletalMeshLODToDynamicMesh(TargetSkeletalMesh, TargetLODIndex, TargetDynamicMesh))
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to extract meshes from skeletal mesh LODs"));
        return false;
    }
    
    // if (!TargetDynamicMesh.Attributes()->HasSkinWeights())
    // {
    //     TargetDynamicMesh.Attributes()->AttachSkinWeightsAttribute("SkinWeights");
    // }
    
    UE::Geometry::FTransferBoneWeights TransferOp(&SourceDynamicMesh, "SkinWeights");

    // TransferOp.TransferMethod = ETransferBoneWeightsMethod::ClosestPointOnSurface;
    
    bool bStatus = TransferOp.TransferWeightsToMesh(TargetDynamicMesh, "SkinWeights");

    if (!bStatus)
    {
        UE_LOG(LogTemp, Error, TEXT("Barycentric skin weight transfer Failed."));
    }
    else
    {
        UE_LOG(LogTemp, Log, TEXT("Barycentric skin weight transfer completed using manual extraction."));
    }

    // TargetSkeletalMesh->MarkPackageDirty();
    
    return bStatus;
}

bool USkeletalMeshWeightTools::CopySkinWeights(USkeletalMesh* SourceSkeletalMesh, USkeletalMesh* DestinationSkeletalMesh)
{
    EditorTransferSkinWeightsBarycentric(SourceSkeletalMesh,0, DestinationSkeletalMesh, 0);

    return true;
}

bool USkeletalMeshWeightTools::FloodWeightsToRoot(USkeletalMesh* SourceSkeletalMesh)
{
    SetAllWeightsToRoot(SourceSkeletalMesh);
    return true;
};

bool USkeletalMeshWeightTools::ImportSkinWeights(USkeletalMesh* SkeletalMesh, const FString& LoadPath)
{
//     TSharedPtr<FSkinIOJsonData> WeightData = ImportSkinWeights(LoadPath);
//
//     if (!WeightData)
//     {
//         UE_LOG(LogTemp, Error, TEXT("[USkeletalMeshWeightTools::ImportSkinWeights] Failed to load Json file"));   
//         return false;
//     }
//
//     // Developer Debugging - Remove later
//     int32 count = 0;
//     for (auto VertexPos : WeightData.Get()->Vertices)
//     {
// //        UE_LOG(LogTemp, Display, TEXT("[%d] %f, %f, %f"), count, VertexPos.X, VertexPos.Y, VertexPos.Z);
//         count+=1;
//     }
//
//     for (auto InflunceEntry : WeightData->Weights)
//     {
// //        UE_LOG(LogTemp, Display, TEXT("[%s]"), *InflunceEntry.Key);
//         for (auto InfluencedVertex : InflunceEntry.Value)
//         {
//             auto VertexPos = WeightData->Vertices[InfluencedVertex.Key];
// //            UE_LOG(LogTemp, Display, TEXT("  [%d][%f, %f, %f] : %f"), InfluencedVertex.Key, VertexPos.X, VertexPos.Y, VertexPos.Z, InfluencedVertex.Value);
//         }
//     }
//     
//     
//     if (!SkeletalMesh || !SkeletalMesh->GetImportedModel())
//     {
//         UE_LOG(LogTemp, Warning, TEXT("Invalid SkeletalMesh"));
//         return false;
//     }
//     
//     FSkeletalMeshModel* ImportedModel = SkeletalMesh->GetImportedModel();
//     FSkeletalMeshLODModel& LODModel = ImportedModel->LODModels[0];
//
//     TArray<FName> OriginalBoneNamesInOrder = SkeletalMesh->GetRefSkeleton().GetRawRefBoneNames();
//     
//     int32 VtxIndex = 0;
//     for (FSkelMeshSection& Section : LODModel.Sections)
//     {
//         // VertexIndex = Index that will be updated
//         for (int VertexIndex = 0; VertexIndex < Section.SoftVertices.Num(); VertexIndex++)
//         {
//             FSoftSkinVertex& Vertex = Section.SoftVertices[VertexIndex];
//         
//             
//             float InfluenceWeight = 0.0f;       // The weight to be applied
//             FString BoneName = "";              // The name of the bone that the weight refers to
//
//             auto OriginalBoneIndex = OriginalBoneNamesInOrder.IndexOfByKey(BoneName); // Bone name to Reference Bone Index
//                        
//             FBoneIndexType InfluenceBoneIndex = 0;
//
//             // Clear all influences
//             FMemory::Memset(Vertex.InfluenceBones, 0, sizeof(Vertex.InfluenceBones));
//             FMemory::Memset(Vertex.InfluenceWeights, 0, sizeof(Vertex.InfluenceWeights));
//             
//             // loop over possible influence entries.
//             for (int InfluenceIndex = 0; InfluenceIndex < MAX_TOTAL_INFLUENCES; InfluenceIndex++)
//             {
//                 // Vertex.InfluenceWeights[InfluenceIndex] = 0;
//                 // Vertex.InfluenceBones[InfluenceIndex] = 0;
//                 // Section.BoneMap[Vertex.InfluenceBones[InfluenceIndex]];                
//
//                 if (InfluenceIndex == 0)
//                 {
//                     Vertex.InfluenceWeights[InfluenceIndex] = 255;
//                     Vertex.InfluenceBones[InfluenceIndex] = 0;
//                 }
//             }
//             
//             
//             // if (VtxIndex >= VerticesArray->Num()) break; // commented out as we do not care if there is a difference as we will be sampling
//     
//     
//             // FMemory::Memset(Vertex.InfluenceBones, 0, sizeof(Vertex.InfluenceBones));
//             // FMemory::Memset(Vertex.InfluenceWeights, 0, sizeof(Vertex.InfluenceWeights));
//             //
//             // int InfIdx = 0;
//             // for (const TSharedPtr<FJsonValue>& InfVal : *InfluencesArray)
//             // {
//             //     if (InfIdx >= MAX_TOTAL_INFLUENCES) break;
//             //
//             //     const TSharedPtr<FJsonObject> InfObj = InfVal->AsObject();
//             //     int32 BoneIdx = InfObj->GetIntegerField(TEXT("BoneIndex"));
//             //     float Weight = InfObj->GetNumberField(TEXT("Weight"));
//             //
//             //     Vertex.InfluenceBones[InfIdx] = (uint8)BoneIdx;
//             //     Vertex.InfluenceWeights[InfIdx] = (uint8)(Weight * 255.f);
//             //     InfIdx++;
//             // }
//         }
//     }
//     
//     // // Mark mesh dirty so UE saves & recompiles
//     SkeletalMesh->InvalidateDeriveDataCacheGUID();
//     SkeletalMesh->Build();
//     SkeletalMesh->MarkPackageDirty();
//     SkeletalMesh->PostEditChange();
//
//     
//
// // -----------------------
//     int LODIndex = 0;
//     
//     // testing updating the SkeletalMeshRenderData
//     FSkeletalMeshRenderData* SkelMeshRenderData = SkeletalMesh->GetResourceForRendering();
//
//     FSkeletalMeshLODRenderData& LODData = SkelMeshRenderData->LODRenderData[LODIndex];
//     const int32 ExpectedNumVerts = LODData.GetNumVertices();
//     uint32 NumBoneInfluences = LODData.GetVertexBufferMaxBoneInfluences();
//     bool bUse16BitBoneIndex = LODData.DoesVertexBufferUse16BitBoneIndex();
//
//     UE_LOG(LogTemp, Display, TEXT("%d, %d, %d"), ExpectedNumVerts, NumBoneInfluences, bUse16BitBoneIndex);
//     
//     
//     if (SkeletalMesh->GetSkinWeightProfiles().Num() > 0)
//     {
//         const int32 TotalVertexCount = SkeletalMesh->GetImportedModel()->LODModels[0].NumVertices;
//         const FSkinWeightProfileInfo& SkinWeightProfile = SkeletalMesh->GetSkinWeightProfiles()[0];
//         const FImportedSkinWeightProfileData& SkinWeightData = SkeletalMesh->GetImportedModel()->LODModels[0].SkinWeightProfiles.FindChecked(SkinWeightProfile.Name);
//         // bFoundProfile = SkinWeightData.SkinWeights.Num() == TotalVertexCount;
//         int32 TotalVertexIndex = 0;
//         for (const FSkelMeshSection& Section : SkeletalMesh->GetImportedModel()->LODModels[0].Sections)
//         {
//             const int32 SectionVertexCount = Section.SoftVertices.Num();
//             //Find the number of vertex skin by this bone
//             for (int32 SectionVertexIndex = 0; SectionVertexIndex < SectionVertexCount; ++SectionVertexIndex, ++TotalVertexIndex)
//             {
//                 const FRawSkinWeight& SkinWeight = SkinWeightData.SkinWeights[TotalVertexIndex];
//                 // IncrementInfluence(Section, SkinWeight.InfluenceBones, SkinWeight.InfluenceWeights);
//                 UE_LOG(LogTemp, Display, TEXT("%p, %p"), SkinWeight.InfluenceBones, SkinWeight.InfluenceWeights);
//             }
//         }
//     }

    
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

TSharedPtr<FSkinIOJsonData> USkeletalMeshWeightTools::ImportSkinWeights( const FString& LoadPath)
{
    TSharedPtr<FSkinIOJsonData> SkinWeights = MakeShared<FSkinIOJsonData>();
    
    FString FileContents;
    if (!FFileHelper::LoadFileToString(FileContents, *LoadPath))
    {
        UE_LOG(LogTemp, Warning, TEXT("Could not load file %s"), *LoadPath);
        return nullptr;
    }

    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(FileContents);

    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to parse JSON"));
        return nullptr;
    }

    const TArray<TSharedPtr<FJsonValue>>* ObjDDic;
    if (!Root->TryGetArrayField(TEXT("ObjDDic"), ObjDDic))
    {
        UE_LOG(LogTemp, Warning, TEXT("No ObjDDic field in JSON"));
        return nullptr;
    }

    for (int32 ObjIndex = 0; ObjIndex < ObjDDic->Num(); ++ObjIndex)
    {
        const TSharedPtr<FJsonObject>& ObjData = (*ObjDDic)[ObjIndex]->AsObject();

        // Weights
        
        const TSharedPtr<FJsonObject>* WeightDataCollection;
        if (ObjData->TryGetObjectField(TEXT("weights"), WeightDataCollection))
        {
            TArray<FString> BoneNames; 
            auto WeightsObject = WeightDataCollection->Get()->Values;
            WeightsObject.GetKeys(BoneNames);

            for (int32 Index = 0; Index < BoneNames.Num(); ++Index)
            {
                FString& BoneName = BoneNames[Index];
                SkinWeights.Get()->Weights.FindOrAdd(BoneName);

//                UE_LOG(LogTemp, Display, TEXT("%s"), *BoneName);

                const TSharedPtr<FJsonObject>* BoneJsonObject;
                if (WeightDataCollection->Get()->TryGetObjectField(BoneName, BoneJsonObject))
                {
                    auto VertJsonData =  BoneJsonObject->Get()->Values;
                    TArray<FString> VerIndices;
                    VertJsonData.GetKeys(VerIndices);

                    for (FString VertIndex : VerIndices)
                    {
                        int VertexI;
                        float VertexWeight;
                        BoneJsonObject->Get()->TryGetNumberField(VertIndex, VertexWeight);

//                        UE_LOG(LogTemp, Display, TEXT("     [%s] %s : %f"), *BoneName, *VertIndex, VertexWeight);

                        LexFromString(VertexI, *VertIndex); // convert FString to Int
                        
                        (*SkinWeights).Weights[BoneName].FindOrAdd(VertexI);
                        (*SkinWeights).Weights[BoneName][VertexI] = VertexWeight;
                    }
                }
            }
        }

        // Vertices
        
        const TArray<TSharedPtr<FJsonValue>>* JsonVerts;
        if (ObjData->TryGetArrayField(TEXT("vertices"), JsonVerts))
        {
            for (const TSharedPtr<FJsonValue>& VertexPositionObj : *JsonVerts)
            {
                const TSharedPtr<FJsonObject> VertObj = VertexPositionObj->AsObject();
                FVector3f VertexPosition = FVector3f( 
                    VertObj->GetNumberField(TEXT("X")),
                    VertObj->GetNumberField(TEXT("Y")),
                    VertObj->GetNumberField(TEXT("Z"))
                    );

                SkinWeights.Get()->Vertices.Add(VertexPosition);
            }
        }
    }
    
    return SkinWeights;
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