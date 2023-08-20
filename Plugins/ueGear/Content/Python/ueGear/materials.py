import unreal

from . import helpers

# Dictionary containing all the default material sample types
MATERIAL_SAMPLER_TYPES = {
    "Color": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    "Grayscale": unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE,
    "Alpha": unreal.MaterialSamplerType.SAMPLERTYPE_ALPHA,
    "Normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    "Masks": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    "DistanceFieldFont": unreal.MaterialSamplerType.SAMPLERTYPE_DISTANCE_FIELD_FONT,
    "LinearColor": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
}

# Dictionary containing all the default Unreal Material properties
MATERIAL_PROPERTIES = {
    "BaseColor": unreal.MaterialProperty.MP_BASE_COLOR,
    "Metallic": unreal.MaterialProperty.MP_METALLIC,
    "Specular": unreal.MaterialProperty.MP_SPECULAR,
    "Roughness": unreal.MaterialProperty.MP_ROUGHNESS,
    "EmissiveColor": unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    "Normal": unreal.MaterialProperty.MP_NORMAL,
}


def create_material(
    material_name,
    material_path,
    diffuse_color=None,
    roughness=None,
    specular=None,
):
    """
    Creates a new Unreal material with given name.

    :param str material_name: name of the material to create.
    :param str material_path: path where material will be created project.
    :param tuple(int, int) or None diffuse_color: default diffuse color for the material.
    :param float or None roughness: default roughness for the material.
    :param float or None specular: default specular for the material.
    :return: newly created material.
    :rtype: unreal.Material
    """

    new_material = (
        unreal.AssetToolsHelpers()
        .get_asset_tools()
        .create_asset(
            material_name,
            material_path,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    )

    if diffuse_color is not None:
        ts_node_diffuse = (
            unreal.MaterialEditingLibrary.create_material_expression(
                new_material, unreal.MaterialExpressionTextureSample, 0, 0
            )
        )
        for color_value, color_channel in zip(diffuse_color, "RGB"):
            ts_node_diffuse.set_editor_property(color_channel, color_value)
        unreal.MaterialEditingLibrary.connect_material_property(
            ts_node_diffuse, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
        )

    if roughness is not None:
        ts_node_roughness = (
            unreal.MaterialEditingLibrary.create_material_expression(
                new_material, unreal.MaterialExpressionConstant, 0, 0
            )
        )
        ts_node_roughness.set_editor_property("R", roughness)
        unreal.MaterialEditingLibrary.connect_material_property(
            ts_node_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
        )

    if specular is not None:
        ts_node_specular = (
            unreal.MaterialEditingLibrary.create_material_expression(
                new_material, unreal.MaterialExpressionConstant, 0, 0
            )
        )
        ts_node_specular.set_editor_property("R", roughness)
        unreal.MaterialEditingLibrary.connect_material_property(
            ts_node_specular, "", unreal.MaterialProperty.MP_SPECULAR
        )

    return new_material


def create_material_texture_sample(
    material,
    pos_x=0,
    pos_y=0,
    texture=None,
    sampler_type=None,
    connect=True,
    from_expression="RGB",
    property_to_connect=unreal.MaterialProperty.MP_BASE_COLOR,
):
    """
    Creates a new material texture sample within the given material.

    :param unreal.Material material: material we want to create texture sample for.
    :param int pos_x:
    :param int  pos_y:
    :param texture:
    :param sampler_type:
    :param connect:
    :param from_expression:
    :param property_to_connect:
    :return:
    """

    material_texture_sample = (
        unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, pos_x, pos_y
        )
    )
    if texture:
        material_texture_sample.set_editor_property("texture", texture)
        if sampler_type is not None and sampler_type != "":
            if helpers.is_string(sampler_type):
                sampler_type = MATERIAL_SAMPLER_TYPES.get(sampler_type, None)
            if sampler_type is not None:
                material_texture_sample.set_editor_property(
                    "sampler_type", sampler_type
                )
    if connect:
        if helpers.is_string(property_to_connect):
            property_to_connect = MATERIAL_PROPERTIES.get(
                property_to_connect, None
            )
        if property_to_connect is not None and property_to_connect != "":
            unreal.MaterialEditingLibrary.connect_material_property(
                material_texture_sample, from_expression, property_to_connect
            )

    return material_texture_sample
