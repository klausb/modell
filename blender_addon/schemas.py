from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = "1.0"


ACTIONS = {
    "ping",
    "health",
    "capabilities",
    "get_scene_summary",
    "list_objects",
    "get_object_info",
    "create_primitive",
    "create_curve_profile",
    "create_parametric_shape",
    "create_freeform_blob",
    "transform_object",
    "set_object_origin",
    "rename_object",
    "duplicate_object",
    "delete_object",
    "apply_modifier_stack_preset",
    "add_modifier",
    "update_modifier",
    "remove_modifier",
    "assign_material",
    "set_material_color",
    "set_surface_structure",
    "set_shading",
    "join_objects",
    "separate_object",
    "boolean_operation",
    "extrude_region",
    "bevel_edges",
    "subdivide_mesh",
    "remesh_object",
    "smooth_mesh",
    "deform_lattice_like",
    "render_preview",
    "export_scene",
}

PARAMETRIC_SHAPES = {"STOOL", "VASE", "TABLE", "BOTTLE", "HANDLE"}
BOOLEAN_OPERATIONS = {"UNION", "DIFFERENCE", "INTERSECT"}
SHADING_MODES = {"FLAT", "SMOOTH", "AUTO"}
MODIFIER_TYPES = {
    "MIRROR",
    "ARRAY",
    "BEVEL",
    "SOLIDIFY",
    "SUBSURF",
    "REMESH",
    "SCREW",
    "SKIN",
    "DECIMATE",
}
MODIFIER_PRESETS = {
    "HARD_SURFACE_CLEAN",
    "SOFT_SUBD",
    "THICK_SHELL",
    "SYMMETRIC_BLOCKOUT",
    "ORGANIC_BLOB",
    "PANELLED_SURFACE",
}
SURFACE_STRUCTURES = {
    "SMOOTH",
    "FACETED",
    "RIBBED",
    "PANELLED",
    "DIMPLED",
    "CREASED",
    "THICKENED",
    "LATTICE_FRAME",
}


@dataclass(slots=True)
class RequestEnvelope:
    protocol_version: str
    request_id: str
    token: str
    action: str
    params: dict[str, Any]


def validate_request(payload: dict[str, Any]) -> RequestEnvelope:
    required = ["protocol_version", "request_id", "token", "action", "params"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing request fields: {', '.join(missing)}")

    protocol_version = str(payload["protocol_version"])
    request_id = str(payload["request_id"])
    token = str(payload["token"])
    action = str(payload["action"])
    params = payload["params"]

    if not isinstance(params, dict):
        raise ValueError("Request params must be an object")
    if action not in ACTIONS:
        raise ValueError(f"Action not allowlisted: {action}")

    return RequestEnvelope(
        protocol_version=protocol_version,
        request_id=request_id,
        token=token,
        action=action,
        params=params,
    )


def make_response(
    *,
    request_id: str,
    ok: bool,
    result: Any = None,
    error: dict[str, Any] | None = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> dict[str, Any]:
    return {
        "protocol_version": protocol_version,
        "request_id": request_id,
        "ok": ok,
        "result": result,
        "error": error,
    }


def make_error(
    *,
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> dict[str, Any]:
    return make_response(
        request_id=request_id,
        ok=False,
        result=None,
        error={
            "code": code,
            "message": message,
            "details": details or {},
        },
        protocol_version=protocol_version,
    )


def capabilities_payload() -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "actions": sorted(ACTIONS),
        "parametric_shape_types": sorted(PARAMETRIC_SHAPES),
        "boolean_operations": sorted(BOOLEAN_OPERATIONS),
        "shading_modes": sorted(SHADING_MODES),
        "modifier_types": sorted(MODIFIER_TYPES),
        "modifier_presets": sorted(MODIFIER_PRESETS),
        "surface_structures": sorted(SURFACE_STRUCTURES),
    }
