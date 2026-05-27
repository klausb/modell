from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModellBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActionName(StrEnum):
    PING = "ping"
    HEALTH = "health"
    CAPABILITIES = "capabilities"
    GET_SCENE_SUMMARY = "get_scene_summary"
    LIST_OBJECTS = "list_objects"
    GET_OBJECT_INFO = "get_object_info"
    CREATE_PRIMITIVE = "create_primitive"
    CREATE_CURVE_PROFILE = "create_curve_profile"
    CREATE_PARAMETRIC_SHAPE = "create_parametric_shape"
    CREATE_FREEFORM_BLOB = "create_freeform_blob"
    TRANSFORM_OBJECT = "transform_object"
    SET_OBJECT_ORIGIN = "set_object_origin"
    RENAME_OBJECT = "rename_object"
    DUPLICATE_OBJECT = "duplicate_object"
    DELETE_OBJECT = "delete_object"
    APPLY_MODIFIER_STACK_PRESET = "apply_modifier_stack_preset"
    ADD_MODIFIER = "add_modifier"
    UPDATE_MODIFIER = "update_modifier"
    REMOVE_MODIFIER = "remove_modifier"
    ASSIGN_MATERIAL = "assign_material"
    SET_MATERIAL_COLOR = "set_material_color"
    SET_SURFACE_STRUCTURE = "set_surface_structure"
    SET_SHADING = "set_shading"
    JOIN_OBJECTS = "join_objects"
    SEPARATE_OBJECT = "separate_object"
    BOOLEAN_OPERATION = "boolean_operation"
    EXTRUDE_REGION = "extrude_region"
    BEVEL_EDGES = "bevel_edges"
    SUBDIVIDE_MESH = "subdivide_mesh"
    REMESH_OBJECT = "remesh_object"
    SMOOTH_MESH = "smooth_mesh"
    DEFORM_LATTICE_LIKE = "deform_lattice_like"
    RENDER_PREVIEW = "render_preview"
    EXPORT_SCENE = "export_scene"


class PrimitiveType(StrEnum):
    CUBE = "CUBE"
    CYLINDER = "CYLINDER"
    SPHERE = "SPHERE"
    CONE = "CONE"
    PLANE = "PLANE"
    TORUS = "TORUS"


class ParametricShapeType(StrEnum):
    STOOL = "STOOL"
    VASE = "VASE"
    TABLE = "TABLE"
    BOTTLE = "BOTTLE"
    HANDLE = "HANDLE"


class BooleanOperationType(StrEnum):
    UNION = "UNION"
    DIFFERENCE = "DIFFERENCE"
    INTERSECT = "INTERSECT"


class ShadingMode(StrEnum):
    FLAT = "FLAT"
    SMOOTH = "SMOOTH"
    AUTO = "AUTO"


class ModifierType(StrEnum):
    MIRROR = "MIRROR"
    ARRAY = "ARRAY"
    BEVEL = "BEVEL"
    SOLIDIFY = "SOLIDIFY"
    SUBSURF = "SUBSURF"
    REMESH = "REMESH"
    SCREW = "SCREW"
    SKIN = "SKIN"
    DECIMATE = "DECIMATE"


class ModifierPreset(StrEnum):
    HARD_SURFACE_CLEAN = "HARD_SURFACE_CLEAN"
    SOFT_SUBD = "SOFT_SUBD"
    THICK_SHELL = "THICK_SHELL"
    SYMMETRIC_BLOCKOUT = "SYMMETRIC_BLOCKOUT"
    ORGANIC_BLOB = "ORGANIC_BLOB"
    PANELLED_SURFACE = "PANELLED_SURFACE"


class SurfaceStructure(StrEnum):
    SMOOTH = "SMOOTH"
    FACETED = "FACETED"
    RIBBED = "RIBBED"
    PANELLED = "PANELLED"
    DIMPLED = "DIMPLED"
    CREASED = "CREASED"
    THICKENED = "THICKENED"
    LATTICE_FRAME = "LATTICE_FRAME"


class Vector3(ModellBaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class ColorRGBA(ModellBaseModel):
    r: float = Field(default=1.0, ge=0.0, le=1.0)
    g: float = Field(default=1.0, ge=0.0, le=1.0)
    b: float = Field(default=1.0, ge=0.0, le=1.0)
    a: float = Field(default=1.0, ge=0.0, le=1.0)


class ObjectRef(ModellBaseModel):
    name: str


class SceneObjectSummary(ModellBaseModel):
    name: str
    type: str
    location: Vector3 = Field(default_factory=Vector3)
    dimensions: Vector3 | None = None
    selected: bool = False


class SceneSummary(ModellBaseModel):
    object_count: int = 0
    selected_count: int = 0
    active_object: str | None = None
    objects: list[SceneObjectSummary] = Field(default_factory=list)


class ObjectInfo(ModellBaseModel):
    name: str
    type: str
    location: Vector3 = Field(default_factory=Vector3)
    rotation: Vector3 = Field(default_factory=Vector3)
    scale: Vector3 = Field(default_factory=Vector3)
    dimensions: Vector3 | None = None
    modifiers: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)


class Capabilities(ModellBaseModel):
    protocol_version: str
    actions: list[ActionName] = Field(default_factory=list)
    primitive_types: list[PrimitiveType] = Field(default_factory=list)
    parametric_shape_types: list[ParametricShapeType] = Field(default_factory=list)
    boolean_operations: list[BooleanOperationType] = Field(default_factory=list)
    shading_modes: list[ShadingMode] = Field(default_factory=list)
    modifier_types: list[ModifierType] = Field(default_factory=list)
    modifier_presets: list[ModifierPreset] = Field(default_factory=list)
    surface_structures: list[SurfaceStructure] = Field(default_factory=list)


class PrimitiveCreateParams(ModellBaseModel):
    primitive_type: PrimitiveType
    name: str | None = None
    location: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: list[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0])
    dimensions: list[float] | None = None
    size: float | None = None
    radius: float | None = None
    depth: float | None = None


class TransformObjectParams(ModellBaseModel):
    object_name: str
    location: list[float] | None = None
    rotation: list[float] | None = None
    scale: list[float] | None = None


class BooleanOperationParams(ModellBaseModel):
    target_object: str
    cutter_object: str
    operation: BooleanOperationType


class ModifierParams(ModellBaseModel):
    object_name: str
    modifier_type: ModifierType
    modifier_name: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class SurfaceStructureParams(ModellBaseModel):
    object_name: str
    structure: SurfaceStructure
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


class MaterialColorParams(ModellBaseModel):
    object_name: str
    color: ColorRGBA


class DeleteObjectParams(ModellBaseModel):
    object_name: str


class CommonResult(ModellBaseModel):
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None
ProtocolParams = dict[str, JsonValue]


class ProtocolErrorDetail(ModellBaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthStatus(ModellBaseModel):
    state: Literal["ok", "degraded", "error"]
    detail: str | None = None