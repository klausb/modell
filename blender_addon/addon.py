from __future__ import annotations

import bpy

from .server import stop_server
from .state import get_state
from .timers import ensure_timer_registered, ensure_timer_unregistered
from .ui import UI_CLASSES


class ModellAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    host: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Host",
        description="Bind host (default localhost only)",
        default="127.0.0.1",
    )
    port: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Port",
        default=8765,
        min=1,
        max=65535,
    )
    token: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Token",
        description="Shared token used by Modell client",
        default="change-me",
        subtype="PASSWORD",
    )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Modell TCP Server")
        layout.prop(self, "host")
        layout.prop(self, "port")
        layout.prop(self, "token")
        layout.label(text="Use 127.0.0.1 by default; expose LAN only intentionally.")


CLASSES = (ModellAddonPreferences, *UI_CLASSES)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    ensure_timer_registered()
    state = get_state()
    state.note_result("addon:registered")


def unregister() -> None:
    stop_server()
    ensure_timer_unregistered()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
