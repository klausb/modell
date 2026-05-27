bl_info = {
    "name": "Modell Remote Control",
    "author": "Modell",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Modell",
    "description": "Remote TCP control endpoint for Modell",
    "category": "3D View",
}


def register() -> None:
    from .addon import register as _register

    _register()


def unregister() -> None:
    from .addon import unregister as _unregister

    _unregister()
