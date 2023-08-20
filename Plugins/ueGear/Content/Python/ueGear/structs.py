import unreal


@unreal.ustruct()
class AssetExportData(unreal.StructBase):
    """
    Struct that contains data related with exported assets
    """

    name = unreal.uproperty(str)
    path = unreal.uproperty(str)
    asset_type = unreal.uproperty(str)
    fbx_file = unreal.uproperty(str)
