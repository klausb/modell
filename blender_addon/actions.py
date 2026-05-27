from __future__ import annotations

import math
from typing import Any

import bmesh
import bpy

from .schemas import (
    BOOLEAN_OPERATIONS,
    MODIFIER_PRESETS,
    MODIFIER_TYPES,
    PARAMETRIC_SHAPES,
    SHADING_MODES,
    SURFACE_STRUCTURES,
)


_MODIFIER_MAP = {
    "MIRROR": "MIRROR",
    "ARRAY": "ARRAY",
    "BEVEL": "BEVEL",
    "SOLIDIFY": "SOLIDIFY",
    "SUBSURF": "SUBSURF",
    "REMESH": "REMESH",
    "SCREW": "SCREW",
    "SKIN": "SKIN",
    "DECIMATE": "DECIMATE",
}


CURVED_RADIAL_SEGMENTS = 64
CURVED_VERTICAL_SEGMENTS = 32
TORUS_MINOR_SEGMENTS = 24


def _vec3(values: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return default
    return float(values[0]), float(values[1]), float(values[2])


def _maybe_vec3(values: Any) -> tuple[float, float, float] | None:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return None
    return float(values[0]), float(values[1]), float(values[2])


def _float_param(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _scene_objects() -> list[bpy.types.Object]:
    return list(bpy.context.scene.objects)


def _get_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Object not found: {name}")
    return obj


def _link_object(obj: bpy.types.Object) -> None:
    bpy.context.scene.collection.objects.link(obj)


def _create_mesh_object(name: str) -> tuple[bpy.types.Object, bmesh.types.BMesh]:
    mesh = bpy.data.meshes.new(name + "Mesh")
    obj = bpy.data.objects.new(name, mesh)
    _link_object(obj)
    bm = bmesh.new()
    return obj, bm


def _finish_bmesh(obj: bpy.types.Object, bm: bmesh.types.BMesh) -> None:
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _basic_object_payload(obj: bpy.types.Object) -> dict[str, Any]:
    return {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def do_ping(_: dict[str, Any]) -> dict[str, Any]:
    return {"message": "pong"}


def do_health(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": "ok",
        "detail": "timer-driven execution active",
    }


def do_get_scene_summary(_: dict[str, Any]) -> dict[str, Any]:
    scene = bpy.context.scene
    objs = _scene_objects()
    active = bpy.context.view_layer.objects.active
    return {
        "object_count": len(objs),
        "selected_count": len(bpy.context.selected_objects),
        "active_object": active.name if active else None,
        "objects": [
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "dimensions": list(obj.dimensions),
                "selected": obj.select_get(),
            }
            for obj in scene.objects
        ],
    }


def do_list_objects(_: dict[str, Any]) -> dict[str, Any]:
    return {"objects": [{"name": obj.name, "type": obj.type} for obj in _scene_objects()]}


def do_get_object_info(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    return {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "dimensions": list(obj.dimensions),
        "modifiers": [mod.name for mod in obj.modifiers],
        "materials": [slot.material.name for slot in obj.material_slots if slot.material],
    }


def do_create_primitive(params: dict[str, Any]) -> dict[str, Any]:
    raw_primitive = params.get("primitive_type")
    if raw_primitive is None:
        raw_primitive = params.get("type")
    if raw_primitive is None:
        raw_primitive = params.get("primitive")
    primitive_type = str(raw_primitive or "CUBE").upper()
    name = str(params.get("name") or f"{primitive_type.title()}Obj")
    location = _vec3(params.get("location"), (0.0, 0.0, 0.0))
    rotation = _vec3(params.get("rotation"), (0.0, 0.0, 0.0))
    scale = _vec3(params.get("scale"), (1.0, 1.0, 1.0))
    dimensions = _maybe_vec3(params.get("dimensions"))

    obj, bm = _create_mesh_object(name)

    if primitive_type == "CUBE":
        size = _float_param(params.get("size"), 1.0)
        bmesh.ops.create_cube(bm, size=size)
    elif primitive_type == "CYLINDER":
        radius = _float_param(params.get("radius"), 0.5)
        depth = _float_param(params.get("depth"), 1.0)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=CURVED_RADIAL_SEGMENTS,
            radius1=radius,
            radius2=radius,
            depth=depth,
        )
    elif primitive_type == "SPHERE":
        radius = _float_param(params.get("radius"), 0.5)
        bmesh.ops.create_uvsphere(
            bm,
            u_segments=CURVED_RADIAL_SEGMENTS,
            v_segments=CURVED_VERTICAL_SEGMENTS,
            radius=radius,
        )
    elif primitive_type == "CONE":
        radius = _float_param(params.get("radius"), 0.5)
        depth = _float_param(params.get("depth"), 1.0)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=CURVED_RADIAL_SEGMENTS,
            radius1=radius,
            radius2=0.0,
            depth=depth,
        )
    elif primitive_type == "PLANE":
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    elif primitive_type == "TORUS":
        bmesh.ops.create_torus(
            bm,
            cap_ends=False,
            cap_tris=False,
            segments=CURVED_RADIAL_SEGMENTS,
            segments_minor=TORUS_MINOR_SEGMENTS,
            radius_major=0.7,
            radius_minor=0.2,
        )
    else:
        bm.free()
        bpy.data.objects.remove(obj, do_unlink=True)
        raise ValueError(f"Unsupported primitive_type: {primitive_type}")

    _finish_bmesh(obj, bm)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    if dimensions is not None:
        obj.dimensions = dimensions

    return {"created": _basic_object_payload(obj), "primitive_type": primitive_type}


def do_create_curve_profile(params: dict[str, Any]) -> dict[str, Any]:
    profile_type = str(params.get("profile_type", "CIRCLE")).upper()
    name = str(params.get("name") or "CurveProfile")
    curve = bpy.data.curves.new(name=name + "Data", type="CURVE")
    curve.dimensions = "3D"
    spline = curve.splines.new(type="BEZIER")
    spline.bezier_points.add(2)
    points = [(-0.4, 0.0, 0.0), (0.0, 0.4, 0.0), (0.4, 0.0, 0.0)]
    for idx, point in enumerate(points):
        p = spline.bezier_points[idx]
        p.co = point
        p.handle_left_type = "AUTO"
        p.handle_right_type = "AUTO"
    if profile_type == "CIRCLE":
        spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    _link_object(obj)
    return {"created": _basic_object_payload(obj), "profile_type": profile_type}


def do_create_parametric_shape(params: dict[str, Any]) -> dict[str, Any]:
    shape = str(params.get("shape_type", "")).upper()
    if shape not in PARAMETRIC_SHAPES:
        raise ValueError(f"shape_type must be one of: {sorted(PARAMETRIC_SHAPES)}")

    created: list[str] = []
    if shape == "STOOL":
        seat = do_create_primitive({"primitive_type": "CYLINDER", "name": "StoolSeat", "scale": [0.6, 0.6, 0.12]})
        created.append(seat["created"]["name"])
        for i in range(4):
            angle = i * (math.pi / 2.0)
            leg = do_create_primitive(
                {
                    "primitive_type": "CYLINDER",
                    "name": f"StoolLeg{i+1}",
                    "location": [math.cos(angle) * 0.4, math.sin(angle) * 0.4, -0.55],
                    "scale": [0.08, 0.08, 0.55],
                }
            )
            created.append(leg["created"]["name"])
    elif shape == "VASE":
        vase = do_create_primitive({"primitive_type": "CYLINDER", "name": "VaseBody", "scale": [0.35, 0.35, 0.8]})
        created.append(vase["created"]["name"])
        do_add_modifier({"object_name": "VaseBody", "modifier_type": "SUBSURF", "settings": {"levels": 2}})
    elif shape == "TABLE":
        top = do_create_primitive({"primitive_type": "CUBE", "name": "TableTop", "scale": [1.2, 0.8, 0.07]})
        created.append(top["created"]["name"])
        for i, (x, y) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
            leg = do_create_primitive(
                {
                    "primitive_type": "CUBE",
                    "name": f"TableLeg{i+1}",
                    "location": [x * 0.95, y * 0.55, -0.75],
                    "scale": [0.07, 0.07, 0.75],
                }
            )
            created.append(leg["created"]["name"])
    elif shape == "BOTTLE":
        body = do_create_primitive({"primitive_type": "CYLINDER", "name": "BottleBody", "scale": [0.28, 0.28, 0.75]})
        neck = do_create_primitive({"primitive_type": "CYLINDER", "name": "BottleNeck", "location": [0, 0, 0.8], "scale": [0.12, 0.12, 0.25]})
        created.extend([body["created"]["name"], neck["created"]["name"]])
    elif shape == "HANDLE":
        handle = do_create_primitive({"primitive_type": "TORUS", "name": "HandleMain", "scale": [0.7, 0.3, 0.2]})
        created.append(handle["created"]["name"])

    return {"shape_type": shape, "objects": created}


def do_create_freeform_blob(params: dict[str, Any]) -> dict[str, Any]:
    name = str(params.get("name") or "FreeformBlob")
    created = do_create_primitive({"primitive_type": "SPHERE", "name": name, "scale": [0.75, 0.68, 0.82]})
    do_add_modifier({"object_name": name, "modifier_type": "REMESH", "settings": {"octree_depth": 5}})
    do_add_modifier({"object_name": name, "modifier_type": "SUBSURF", "settings": {"levels": 1}})
    return {"created": created["created"], "note": "Blob created with remesh/subsurf stack"}


def do_transform_object(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    if "location" in params:
        obj.location = _vec3(params.get("location"), tuple(obj.location))
    if "rotation" in params:
        obj.rotation_euler = _vec3(params.get("rotation"), tuple(obj.rotation_euler))
    if "scale" in params:
        obj.scale = _vec3(params.get("scale"), tuple(obj.scale))
    return {"updated": _basic_object_payload(obj)}


def do_set_object_origin(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    origin = _vec3(params.get("origin"), tuple(obj.location))
    obj.location = origin
    return {"updated": _basic_object_payload(obj), "note": "Origin approximated by location assignment"}


def do_rename_object(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    new_name = str(params.get("new_name", "")).strip()
    if not new_name:
        raise ValueError("new_name is required")
    old = obj.name
    obj.name = new_name
    return {"old_name": old, "new_name": obj.name}


def do_duplicate_object(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    dup = obj.copy()
    if obj.data:
        dup.data = obj.data.copy()
    dup.name = str(params.get("new_name") or f"{obj.name}_copy")
    _link_object(dup)
    offset = _vec3(params.get("offset"), (0.25, 0.25, 0.0))
    dup.location = (obj.location.x + offset[0], obj.location.y + offset[1], obj.location.z + offset[2])
    return {"duplicated": _basic_object_payload(dup)}


def do_delete_object(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    name = obj.name
    bpy.data.objects.remove(obj, do_unlink=True)
    return {"deleted": name}


def do_add_modifier(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    modifier_type = str(params.get("modifier_type", "")).upper()
    if modifier_type not in MODIFIER_TYPES:
        raise ValueError(f"modifier_type must be one of: {sorted(MODIFIER_TYPES)}")
    modifier_name = str(params.get("modifier_name") or f"{modifier_type}_Mod")
    mod = obj.modifiers.new(name=modifier_name, type=_MODIFIER_MAP[modifier_type])

    settings = params.get("settings", {})
    if isinstance(settings, dict):
        for key, value in settings.items():
            if hasattr(mod, key):
                setattr(mod, key, value)
    return {"object_name": obj.name, "modifier": mod.name, "modifier_type": modifier_type}


def do_update_modifier(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    modifier_name = str(params.get("modifier_name", "")).strip()
    if not modifier_name:
        raise ValueError("modifier_name is required")
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"Modifier not found: {modifier_name}")

    modifier_type = str(params.get("modifier_type", "")).upper()
    if modifier_type and modifier_type not in MODIFIER_TYPES:
        raise ValueError(f"modifier_type must be one of: {sorted(MODIFIER_TYPES)}")

    settings = params.get("settings", {})
    if isinstance(settings, dict):
        for key, value in settings.items():
            if hasattr(mod, key):
                setattr(mod, key, value)
    return {"object_name": obj.name, "modifier": mod.name, "updated": True}


def do_remove_modifier(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    modifier_name = str(params.get("modifier_name", "")).strip()
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"Modifier not found: {modifier_name}")
    obj.modifiers.remove(mod)
    return {"object_name": obj.name, "removed_modifier": modifier_name}


def do_apply_modifier_stack_preset(params: dict[str, Any]) -> dict[str, Any]:
    object_name = str(params.get("object_name", ""))
    preset = str(params.get("preset", "")).upper()
    if preset not in MODIFIER_PRESETS:
        raise ValueError(f"preset must be one of: {sorted(MODIFIER_PRESETS)}")

    plan: dict[str, list[dict[str, Any]]] = {
        "HARD_SURFACE_CLEAN": [{"modifier_type": "BEVEL", "settings": {"width": 0.02}}, {"modifier_type": "WEIGHTED_NORMAL", "settings": {}}],
        "SOFT_SUBD": [{"modifier_type": "SUBSURF", "settings": {"levels": 2}}],
        "THICK_SHELL": [{"modifier_type": "SOLIDIFY", "settings": {"thickness": 0.03}}],
        "SYMMETRIC_BLOCKOUT": [{"modifier_type": "MIRROR", "settings": {"use_axis": [True, False, False]}}, {"modifier_type": "BEVEL", "settings": {"width": 0.03}}],
        "ORGANIC_BLOB": [{"modifier_type": "REMESH", "settings": {"octree_depth": 5}}, {"modifier_type": "SUBSURF", "settings": {"levels": 1}}],
        "PANELLED_SURFACE": [{"modifier_type": "SOLIDIFY", "settings": {"thickness": 0.02}}, {"modifier_type": "BEVEL", "settings": {"width": 0.01}}],
    }
    applied: list[str] = []
    for step in plan[preset]:
        mtype = step["modifier_type"]
        if mtype not in MODIFIER_TYPES:
            # Weighted normal is not in the strict allowlist; skip rather than bypass constraints.
            continue
        result = do_add_modifier(
            {
                "object_name": object_name,
                "modifier_type": mtype,
                "settings": step.get("settings", {}),
            }
        )
        applied.append(str(result["modifier"]))
    return {"object_name": object_name, "preset": preset, "applied": applied}


def do_assign_material(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    material_name = str(params.get("material_name") or "ModellMaterial")
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
    if obj.data and hasattr(obj.data, "materials"):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    return {"object_name": obj.name, "material": mat.name}


def do_set_material_color(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    if not obj.material_slots or not obj.material_slots[0].material:
        do_assign_material({"object_name": obj.name, "material_name": f"{obj.name}_Mat"})
    mat = obj.material_slots[0].material
    color = params.get("color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
    rgba = (
        float(color.get("r", 1.0)),
        float(color.get("g", 1.0)),
        float(color.get("b", 1.0)),
        float(color.get("a", 1.0)),
    )
    if mat and mat.use_nodes and mat.node_tree:
        principled = mat.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = rgba
    return {"object_name": obj.name, "color": list(rgba)}


def do_set_surface_structure(params: dict[str, Any]) -> dict[str, Any]:
    object_name = str(params.get("object_name", ""))
    structure = str(params.get("structure", "")).upper()
    intensity = float(params.get("intensity", 0.5))
    intensity = max(0.0, min(1.0, intensity))
    if structure not in SURFACE_STRUCTURES:
        raise ValueError(f"structure must be one of: {sorted(SURFACE_STRUCTURES)}")

    if structure == "SMOOTH":
        do_set_shading({"object_name": object_name, "mode": "SMOOTH"})
    elif structure == "FACETED":
        do_set_shading({"object_name": object_name, "mode": "FLAT"})
    elif structure == "RIBBED":
        do_add_modifier({"object_name": object_name, "modifier_type": "SCREW", "settings": {"screw_offset": 0.05 + 0.2 * intensity}})
    elif structure == "PANELLED":
        do_add_modifier({"object_name": object_name, "modifier_type": "BEVEL", "settings": {"width": 0.005 + 0.03 * intensity}})
    elif structure == "DIMPLED":
        do_add_modifier({"object_name": object_name, "modifier_type": "REMESH", "settings": {"octree_depth": int(4 + intensity * 3)}})
    elif structure == "CREASED":
        do_add_modifier({"object_name": object_name, "modifier_type": "BEVEL", "settings": {"segments": int(1 + intensity * 3), "width": 0.01}})
    elif structure == "THICKENED":
        do_add_modifier({"object_name": object_name, "modifier_type": "SOLIDIFY", "settings": {"thickness": 0.01 + 0.08 * intensity}})
    elif structure == "LATTICE_FRAME":
        do_add_modifier({"object_name": object_name, "modifier_type": "SKIN", "settings": {}})

    return {"object_name": object_name, "structure": structure, "intensity": intensity}


def do_set_shading(params: dict[str, Any]) -> dict[str, Any]:
    obj = _get_object(str(params.get("object_name", "")))
    mode = str(params.get("mode", "")).upper()
    if mode not in SHADING_MODES:
        raise ValueError(f"mode must be one of: {sorted(SHADING_MODES)}")
    if obj.type != "MESH" or not obj.data:
        raise ValueError("set_shading requires a mesh object")
    mesh = obj.data
    if mode == "FLAT":
        for poly in mesh.polygons:
            poly.use_smooth = False
    elif mode == "SMOOTH":
        for poly in mesh.polygons:
            poly.use_smooth = True
    elif mode == "AUTO":
        for poly in mesh.polygons:
            poly.use_smooth = True
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
        if hasattr(mesh, "auto_smooth_angle"):
            mesh.auto_smooth_angle = math.radians(35.0)
    mesh.update()
    return {"object_name": obj.name, "mode": mode}


def do_join_objects(params: dict[str, Any]) -> dict[str, Any]:
    names = params.get("object_names", [])
    if not isinstance(names, list) or len(names) < 2:
        raise ValueError("object_names must contain at least two object names")
    target = _get_object(str(names[0]))
    members = [_get_object(str(name)) for name in names]
    mesh_members = [obj for obj in members if obj.type == "MESH"]
    if len(mesh_members) < 2:
        raise ValueError("join_objects requires at least two mesh objects")

    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_members:
        obj.select_set(True)
    view_layer.objects.active = target

    before_names = {obj.name for obj in mesh_members}
    bpy.ops.object.join()
    after_names = {obj.name for obj in bpy.context.scene.objects}
    removed = sorted(name for name in before_names if name not in after_names and name != target.name)
    return {"target": target.name, "joined": removed}


def do_separate_object(params: dict[str, Any]) -> dict[str, Any]:
    _ = params
    return {
        "ok": False,
        "todo": "TODO: separate_object deterministic split strategy not yet implemented",
    }


def do_boolean_operation(params: dict[str, Any]) -> dict[str, Any]:
    target = _get_object(str(params.get("target_object", "")))
    cutter = _get_object(str(params.get("cutter_object", "")))
    operation = str(params.get("operation", "")).upper()
    if operation not in BOOLEAN_OPERATIONS:
        raise ValueError(f"operation must be one of: {sorted(BOOLEAN_OPERATIONS)}")

    modifier = target.modifiers.new(name="BooleanOp", type="BOOLEAN")
    modifier.object = cutter
    modifier.operation = operation
    return {
        "target_object": target.name,
        "cutter_object": cutter.name,
        "operation": operation,
        "note": "Boolean modifier added (non-destructive).",
    }


def _edit_bmesh_object(object_name: str) -> tuple[bpy.types.Object, bmesh.types.BMesh]:
    obj = _get_object(object_name)
    if obj.type != "MESH":
        raise ValueError("Action requires mesh object")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    return obj, bm


def _write_bmesh_object(obj: bpy.types.Object, bm: bmesh.types.BMesh) -> None:
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def do_extrude_region(params: dict[str, Any]) -> dict[str, Any]:
    obj, bm = _edit_bmesh_object(str(params.get("object_name", "")))
    amount = float(params.get("amount", 0.1))
    faces = [f for f in bm.faces if f.select] or list(bm.faces)
    if not faces:
        bm.free()
        raise ValueError("No faces available to extrude")
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts = [elem for elem in ret["geom"] if isinstance(elem, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(0.0, 0.0, amount))
    _write_bmesh_object(obj, bm)
    return {"object_name": obj.name, "extrude_amount": amount}


def do_bevel_edges(params: dict[str, Any]) -> dict[str, Any]:
    obj, bm = _edit_bmesh_object(str(params.get("object_name", "")))
    offset = float(params.get("offset", 0.02))
    segments = int(params.get("segments", 2))
    edges = [e for e in bm.edges if e.select] or list(bm.edges)
    bmesh.ops.bevel(bm, geom=edges, offset=offset, segments=max(1, segments), affect="EDGES")
    _write_bmesh_object(obj, bm)
    return {"object_name": obj.name, "offset": offset, "segments": segments}


def do_subdivide_mesh(params: dict[str, Any]) -> dict[str, Any]:
    obj, bm = _edit_bmesh_object(str(params.get("object_name", "")))
    cuts = int(params.get("cuts", 1))
    edges = list(bm.edges)
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=max(1, cuts), use_grid_fill=True)
    _write_bmesh_object(obj, bm)
    return {"object_name": obj.name, "cuts": cuts}


def do_remesh_object(params: dict[str, Any]) -> dict[str, Any]:
    object_name = str(params.get("object_name", ""))
    depth = int(params.get("octree_depth", 5))
    return do_add_modifier(
        {
            "object_name": object_name,
            "modifier_type": "REMESH",
            "settings": {"octree_depth": max(1, min(8, depth))},
        }
    )


def do_smooth_mesh(params: dict[str, Any]) -> dict[str, Any]:
    obj, bm = _edit_bmesh_object(str(params.get("object_name", "")))
    factor = float(params.get("factor", 0.5))
    factor = max(0.0, min(1.0, factor))
    bmesh.ops.smooth_vert(bm, verts=list(bm.verts), factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    _write_bmesh_object(obj, bm)
    return {"object_name": obj.name, "factor": factor}


def do_deform_lattice_like(params: dict[str, Any]) -> dict[str, Any]:
    object_name = str(params.get("object_name", ""))
    strength = float(params.get("strength", 0.5))
    strength = max(0.0, min(1.0, strength))
    # Deterministic approximation with smooth + subsurf instead of dynamic lattice setup.
    smooth = do_smooth_mesh({"object_name": object_name, "factor": 0.2 + 0.6 * strength})
    subd = do_add_modifier({"object_name": object_name, "modifier_type": "SUBSURF", "settings": {"levels": 1}})
    return {"object_name": object_name, "smooth": smooth, "subsurf": subd}


def do_render_preview(params: dict[str, Any]) -> dict[str, Any]:
    path = str(params.get("filepath") or "//modell_preview.png")
    scene = bpy.context.scene
    old_path = scene.render.filepath
    try:
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        scene.render.filepath = old_path
    return {"preview_path": path}


def do_export_scene(params: dict[str, Any]) -> dict[str, Any]:
    export_format = str(params.get("format", "GLB")).upper()
    filepath = str(params.get("filepath") or "//modell_scene.glb")
    if export_format == "GLB":
        bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB")
    elif export_format == "OBJ":
        bpy.ops.wm.obj_export(filepath=filepath)
    else:
        return {
            "ok": False,
            "todo": "TODO: export_scene supports GLB and OBJ in this phase",
            "requested_format": export_format,
        }
    return {"filepath": filepath, "format": export_format}


ACTION_HANDLERS = {
    "ping": do_ping,
    "health": do_health,
    "capabilities": lambda _: {"note": "capabilities handled by server layer"},
    "get_scene_summary": do_get_scene_summary,
    "list_objects": do_list_objects,
    "get_object_info": do_get_object_info,
    "create_primitive": do_create_primitive,
    "create_curve_profile": do_create_curve_profile,
    "create_parametric_shape": do_create_parametric_shape,
    "create_freeform_blob": do_create_freeform_blob,
    "transform_object": do_transform_object,
    "set_object_origin": do_set_object_origin,
    "rename_object": do_rename_object,
    "duplicate_object": do_duplicate_object,
    "delete_object": do_delete_object,
    "apply_modifier_stack_preset": do_apply_modifier_stack_preset,
    "add_modifier": do_add_modifier,
    "update_modifier": do_update_modifier,
    "remove_modifier": do_remove_modifier,
    "assign_material": do_assign_material,
    "set_material_color": do_set_material_color,
    "set_surface_structure": do_set_surface_structure,
    "set_shading": do_set_shading,
    "join_objects": do_join_objects,
    "separate_object": do_separate_object,
    "boolean_operation": do_boolean_operation,
    "extrude_region": do_extrude_region,
    "bevel_edges": do_bevel_edges,
    "subdivide_mesh": do_subdivide_mesh,
    "remesh_object": do_remesh_object,
    "smooth_mesh": do_smooth_mesh,
    "deform_lattice_like": do_deform_lattice_like,
    "render_preview": do_render_preview,
    "export_scene": do_export_scene,
}
