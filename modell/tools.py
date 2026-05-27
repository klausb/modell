from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from modell.config import AgentConfig
from modell.models import ActionName
from modell.tcp_client import TCPClient


ConfirmCallback = Callable[[str], bool]


@dataclass(slots=True)
class ModellTools:
    client: TCPClient
    agent_config: AgentConfig
    confirm_callback: ConfirmCallback | None = None

    def _call(self, action: ActionName | str, params: dict[str, Any] | None = None) -> Any:
        return self.client.request(action, params or {})

    def _confirm_if_needed(self, action: ActionName, reason: str) -> None:
        destructive_actions = {
            ActionName.DELETE_OBJECT,
            ActionName.BOOLEAN_OPERATION,
            ActionName.SEPARATE_OBJECT,
        }
        if action not in destructive_actions:
            return
        if not self.agent_config.require_confirmation_for_destructive:
            return
        if self.confirm_callback is None:
            raise RuntimeError(
                f"Destructive action '{action.value}' requires confirmation but no callback is configured"
            )
        if not self.confirm_callback(reason):
            raise RuntimeError(f"Destructive action '{action.value}' cancelled")

    def ping(self) -> Any:
        return self._call(ActionName.PING)

    def health(self) -> Any:
        return self._call(ActionName.HEALTH)

    def capabilities(self) -> Any:
        return self._call(ActionName.CAPABILITIES)

    def get_scene_summary(self) -> Any:
        return self._call(ActionName.GET_SCENE_SUMMARY)

    def list_objects(self) -> Any:
        return self._call(ActionName.LIST_OBJECTS)

    def get_object_info(self, object_name: str) -> Any:
        return self._call(ActionName.GET_OBJECT_INFO, {"object_name": object_name})

    def create_primitive(self, **params: Any) -> Any:
        return self._call(ActionName.CREATE_PRIMITIVE, params)

    def create_curve_profile(self, **params: Any) -> Any:
        return self._call(ActionName.CREATE_CURVE_PROFILE, params)

    def create_parametric_shape(self, **params: Any) -> Any:
        return self._call(ActionName.CREATE_PARAMETRIC_SHAPE, params)

    def create_freeform_blob(self, **params: Any) -> Any:
        return self._call(ActionName.CREATE_FREEFORM_BLOB, params)

    def transform_object(self, **params: Any) -> Any:
        return self._call(ActionName.TRANSFORM_OBJECT, params)

    def set_object_origin(self, **params: Any) -> Any:
        return self._call(ActionName.SET_OBJECT_ORIGIN, params)

    def rename_object(self, **params: Any) -> Any:
        return self._call(ActionName.RENAME_OBJECT, params)

    def duplicate_object(self, **params: Any) -> Any:
        return self._call(ActionName.DUPLICATE_OBJECT, params)

    def delete_object(self, **params: Any) -> Any:
        self._confirm_if_needed(ActionName.DELETE_OBJECT, "Delete object")
        return self._call(ActionName.DELETE_OBJECT, params)

    def apply_modifier_stack_preset(self, **params: Any) -> Any:
        return self._call(ActionName.APPLY_MODIFIER_STACK_PRESET, params)

    def add_modifier(self, **params: Any) -> Any:
        return self._call(ActionName.ADD_MODIFIER, params)

    def update_modifier(self, **params: Any) -> Any:
        return self._call(ActionName.UPDATE_MODIFIER, params)

    def remove_modifier(self, **params: Any) -> Any:
        return self._call(ActionName.REMOVE_MODIFIER, params)

    def assign_material(self, **params: Any) -> Any:
        return self._call(ActionName.ASSIGN_MATERIAL, params)

    def set_material_color(self, **params: Any) -> Any:
        return self._call(ActionName.SET_MATERIAL_COLOR, params)

    def set_surface_structure(self, **params: Any) -> Any:
        return self._call(ActionName.SET_SURFACE_STRUCTURE, params)

    def set_shading(self, **params: Any) -> Any:
        return self._call(ActionName.SET_SHADING, params)

    def join_objects(self, **params: Any) -> Any:
        return self._call(ActionName.JOIN_OBJECTS, params)

    def separate_object(self, **params: Any) -> Any:
        self._confirm_if_needed(ActionName.SEPARATE_OBJECT, "Separate object")
        return self._call(ActionName.SEPARATE_OBJECT, params)

    def boolean_operation(self, **params: Any) -> Any:
        self._confirm_if_needed(ActionName.BOOLEAN_OPERATION, "Boolean operation")
        return self._call(ActionName.BOOLEAN_OPERATION, params)

    def extrude_region(self, **params: Any) -> Any:
        return self._call(ActionName.EXTRUDE_REGION, params)

    def bevel_edges(self, **params: Any) -> Any:
        return self._call(ActionName.BEVEL_EDGES, params)

    def subdivide_mesh(self, **params: Any) -> Any:
        return self._call(ActionName.SUBDIVIDE_MESH, params)

    def remesh_object(self, **params: Any) -> Any:
        return self._call(ActionName.REMESH_OBJECT, params)

    def smooth_mesh(self, **params: Any) -> Any:
        return self._call(ActionName.SMOOTH_MESH, params)

    def deform_lattice_like(self, **params: Any) -> Any:
        return self._call(ActionName.DEFORM_LATTICE_LIKE, params)

    def render_preview(self, **params: Any) -> Any:
        return self._call(ActionName.RENDER_PREVIEW, params)

    def export_scene(self, **params: Any) -> Any:
        return self._call(ActionName.EXPORT_SCENE, params)

    def blockout_furniture_piece(
        self,
        description: str,
        dimensions_hint: list[float] | None = None,
        style_hint: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "shape_type": "TABLE",
            "description": description,
            "dimensions_hint": dimensions_hint or [1.0, 0.6, 0.75],
        }
        if style_hint:
            params["style_hint"] = style_hint
        return self.create_parametric_shape(**params)

    def create_organic_container(
        self,
        description: str,
        height: float | None = None,
        width: float | None = None,
        neck_ratio: float | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "shape_type": "VASE",
            "description": description,
            "height": height if height is not None else 1.0,
            "width": width if width is not None else 0.5,
        }
        if neck_ratio is not None:
            params["neck_ratio"] = neck_ratio
        return self.create_parametric_shape(**params)

    def refine_surface_finish(self, object_name: str, finish_style: str, intensity: float = 0.5) -> Any:
        structure = finish_style.upper()
        if structure not in {
            "SMOOTH",
            "FACETED",
            "RIBBED",
            "PANELLED",
            "DIMPLED",
            "CREASED",
            "THICKENED",
            "LATTICE_FRAME",
        }:
            structure = "SMOOTH"
        return self.set_surface_structure(
            object_name=object_name,
            structure=structure,
            intensity=float(max(0.0, min(1.0, intensity))),
        )

    def symmetrize_and_thicken(self, object_name: str, thickness: float) -> dict[str, Any]:
        mirror_result = self.add_modifier(
            object_name=object_name,
            modifier_type="MIRROR",
            settings={"use_axis": [True, False, False]},
        )
        solidify_result = self.add_modifier(
            object_name=object_name,
            modifier_type="SOLIDIFY",
            settings={"thickness": thickness},
        )
        return {"mirror": mirror_result, "solidify": solidify_result}

    def make_low_poly(self, object_name: str, target_strength: float = 0.5) -> dict[str, Any]:
        ratio = max(0.01, 1.0 - min(1.0, target_strength))
        decimate_result = self.add_modifier(
            object_name=object_name,
            modifier_type="DECIMATE",
            settings={"ratio": ratio},
        )
        shading_result = self.set_shading(object_name=object_name, mode="FLAT")
        return {"decimate": decimate_result, "shading": shading_result}

    def preview_and_describe_scene(self) -> dict[str, Any]:
        summary = self.get_scene_summary()
        preview = self.render_preview()
        return {
            "scene_summary": summary,
            "preview": preview,
            "description": "Scene summary and preview captured.",
        }


def build_toolkit(
    client: TCPClient,
    agent_config: AgentConfig,
    *,
    confirm_callback: ConfirmCallback | None = None,
) -> ModellTools:
    return ModellTools(client=client, agent_config=agent_config, confirm_callback=confirm_callback)
