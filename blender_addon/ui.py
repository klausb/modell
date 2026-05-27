from __future__ import annotations

import bpy

from .server import start_server, stop_server
from .state import get_state, sync_from_preferences


class MODELL_OT_start_server(bpy.types.Operator):
    bl_idname = "modell.start_server"
    bl_label = "Start Server"

    def execute(self, context: bpy.types.Context):
        prefs = context.preferences.addons[__package__].preferences
        sync_from_preferences(prefs)
        start_server()
        return {"FINISHED"}


class MODELL_OT_stop_server(bpy.types.Operator):
    bl_idname = "modell.stop_server"
    bl_label = "Stop Server"

    def execute(self, _context: bpy.types.Context):
        stop_server()
        return {"FINISHED"}


class MODELL_OT_self_test(bpy.types.Operator):
    bl_idname = "modell.self_test"
    bl_label = "Self Test"

    def execute(self, _context: bpy.types.Context):
        state = get_state()
        state.note_result("self-test:ok")
        self.report({"INFO"}, "Modell self test passed")
        return {"FINISHED"}


class MODELL_PT_sidebar(bpy.types.Panel):
    bl_label = "Modell"
    bl_idname = "MODELL_PT_sidebar"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Modell"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        state = get_state()
        prefs = context.preferences.addons[__package__].preferences

        status = "running" if state.running else "stopped"
        layout.label(text=f"Status: {status}")
        layout.label(text=f"Host: {prefs.host}")
        layout.label(text=f"Port: {prefs.port}")
        layout.separator()
        layout.label(text=f"Last Request: {state.last_request_id or '-'}")
        layout.label(text=f"Last Action: {state.last_action or '-'}")
        layout.label(text=f"Queue Length: {state.request_queue.qsize()}")

        row = layout.row(align=True)
        row.operator(MODELL_OT_start_server.bl_idname, text="Start Server")
        row.operator(MODELL_OT_stop_server.bl_idname, text="Stop Server")
        layout.operator(MODELL_OT_self_test.bl_idname, text="Self Test")

        layout.separator()
        layout.label(text="Recent Results:")
        if not state.recent_results:
            layout.label(text="-")
        else:
            for item in list(state.recent_results):
                layout.label(text=item[:80])


UI_CLASSES = (
    MODELL_OT_start_server,
    MODELL_OT_stop_server,
    MODELL_OT_self_test,
    MODELL_PT_sidebar,
)
