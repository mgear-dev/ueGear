import unreal

UEGEAR_AVAILABLE = False

unreal.log("Loading ueGear Python Commands...")
try:
    import ueGear.commands

    UEGEAR_AVAILABLE = True
except ImportError as exc:
    unreal.log_error(
        "Something went wrong while importing ueGear Python commands: {}".format(
            exc
        )
    )
finally:
    if UEGEAR_AVAILABLE:
        unreal.log("ueGear Python Commands loaded successfully!")
