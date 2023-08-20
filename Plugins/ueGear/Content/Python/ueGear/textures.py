import unreal

from . import helpers, assets


def generate_texture_import_task(
    filename,
    destination_path,
    destination_name=None,
    replace_existing=True,
    automated=True,
    save=True,
    import_options=None,
):
    """
    Creates and configures an Unreal AssetImportTask to import a texture file.

    :param str filename: texture file to import.
    :param str destination_path: Content Browser path where the asset will be placed.
    :param str or None destination_name: optional name of the imported texture. If not given, the name will be the
            file name without the extension.
    :param bool replace_existing:
    :param bool automated:
    :param bool save:
    :param dict import_options: dictionary containing all the texture settings to use.
    :return: Unreal AssetImportTask that handles the import of the texture file.
    :rtype: unreal.AssetImportTask
    """

    task = unreal.AssetImportTask()
    task.filename = filename
    task.destination_path = destination_path

    # By default, task.destination_name is the filename without the extension
    if destination_name:
        task.destination_name = destination_name

    task.replace_existing = replace_existing
    task.automated = automated
    task.save = save

    texture_factory = unreal.TextureFactory()
    task.factory = texture_factory
    import_options = import_options or dict()
    for name, value in import_options.items():
        try:
            task.factory.set_editor_property(name, value)
        except Exception:
            unreal.log_warning(
                "Was not possible to set FBX Import property: {}: {}".format(
                    name, value
                )
            )

    return task


def import_texture_asset(
    filename, destination_path, destination_name=None, import_options=None
):
    """
    Imports a texture asset into Unreal Content Browser.

    :param str filename: texture file to import.
    :param str destination_path: Content Browser path where the texture will be placed.
    :param str or None destination_name: optional name of the imported texture. If not given, the name will be the
            filename without the extension.
    :param dict import_options: dictionary containing all the texture import settings to use.
    :return: path to the imported texture asset.
    :rtype: str
    """

    tasks = list()
    tasks.append(
        generate_texture_import_task(
            filename,
            destination_path,
            destination_name=destination_name,
            import_options=import_options,
        )
    )

    return helpers.get_first_in_list(assets.import_assets(tasks), default="")
