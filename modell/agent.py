from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modell.config import ModellConfig
from modell.llm import DeterministicEchoLLM, build_smolagents_model
from modell.prompts import SYSTEM_PROMPT
from modell.tools import ModellTools


@dataclass(slots=True)
class AgentRuntime:
    config: ModellConfig
    tools: ModellTools
    _smol_agent: Any | None = None

    def __post_init__(self) -> None:
        self._smol_agent = self._try_build_smol_agent()

    def _try_build_smol_agent(self) -> Any | None:
        try:
            from smolagents import ToolCallingAgent  # type: ignore
        except Exception:
            return None

        try:
            model = build_smolagents_model(self.config.llm)
        except Exception:
            return None

        tool_map = self._tool_map_for_agent()
        tool_functions = [
            _make_agent_tool(func_name, func)
            for func_name, func in tool_map.items()
        ]

        try:
            return ToolCallingAgent(
                model=model,
                tools=tool_functions,
                max_steps=self.config.agent.max_steps,
                system_prompt=SYSTEM_PROMPT,
                verbosity_level=self.config.agent.verbosity,
                planning_interval=self.config.agent.planning_interval,
            )
        except TypeError:
            return None

    def _tool_map_for_agent(self) -> dict[str, Any]:
        return {
            "ping": self.tools.ping,
            "health": self.tools.health,
            "capabilities": self.tools.capabilities,
            "get_scene_summary": self.tools.get_scene_summary,
            "list_objects": self.tools.list_objects,
            "get_object_info": self.tools.get_object_info,
            "create_primitive": self.tools.create_primitive,
            "create_curve_profile": self.tools.create_curve_profile,
            "create_parametric_shape": self.tools.create_parametric_shape,
            "create_freeform_blob": self.tools.create_freeform_blob,
            "transform_object": self.tools.transform_object,
            "set_object_origin": self.tools.set_object_origin,
            "rename_object": self.tools.rename_object,
            "duplicate_object": self.tools.duplicate_object,
            "delete_object": self.tools.delete_object,
            "apply_modifier_stack_preset": self.tools.apply_modifier_stack_preset,
            "add_modifier": self.tools.add_modifier,
            "update_modifier": self.tools.update_modifier,
            "remove_modifier": self.tools.remove_modifier,
            "assign_material": self.tools.assign_material,
            "set_material_color": self.tools.set_material_color,
            "set_surface_structure": self.tools.set_surface_structure,
            "set_shading": self.tools.set_shading,
            "join_objects": self.tools.join_objects,
            "separate_object": self.tools.separate_object,
            "boolean_operation": self.tools.boolean_operation,
            "extrude_region": self.tools.extrude_region,
            "bevel_edges": self.tools.bevel_edges,
            "subdivide_mesh": self.tools.subdivide_mesh,
            "remesh_object": self.tools.remesh_object,
            "smooth_mesh": self.tools.smooth_mesh,
            "deform_lattice_like": self.tools.deform_lattice_like,
            "render_preview": self.tools.render_preview,
            "export_scene": self.tools.export_scene,
            "blockout_furniture_piece": self.tools.blockout_furniture_piece,
            "create_organic_container": self.tools.create_organic_container,
            "refine_surface_finish": self.tools.refine_surface_finish,
            "symmetrize_and_thicken": self.tools.symmetrize_and_thicken,
            "make_low_poly": self.tools.make_low_poly,
            "preview_and_describe_scene": self.tools.preview_and_describe_scene,
        }

    def run(self, user_prompt: str, planning_enabled: bool = True) -> str:
        if self._smol_agent is not None:
            prefix = "Plan mode: ON. " if planning_enabled else "Plan mode: OFF. "
            result = self._smol_agent.run(prefix + user_prompt)
            return str(result)

        return self._fallback_run(user_prompt, planning_enabled)

    def _fallback_run(self, user_prompt: str, planning_enabled: bool) -> str:
        # Safe deterministic fallback while preserving inspect-first behavior.
        summary = self.tools.get_scene_summary()
        low_prompt = user_prompt.lower()
        plan_lines = [
            "Inspection complete.",
            "No smolagents runtime available; deterministic fallback is active.",
        ]

        if "stool" in low_prompt:
            if planning_enabled:
                plan_lines.append("Plan: create parametric stool, then preview scene.")
            created = self.tools.create_parametric_shape(shape_type="STOOL", description=user_prompt)
            preview = self.tools.render_preview()
            return f"{' '.join(plan_lines)}\nCreated: {created}\nPreview: {preview}\nSummary: {summary}"

        llm_stub = DeterministicEchoLLM()
        clarification = llm_stub.complete(
            "Ask user for clarification with available object names and intended operation.",
            system_prompt=SYSTEM_PROMPT,
        )
        return f"{' '.join(plan_lines)}\nSummary: {summary}\n{clarification}"


def _make_agent_tool(name: str, fn: Any) -> Any:
    """Return a smolagents-compatible callable.

    TODO: If your smolagents version requires specific decorators (for example `@tool`),
    wrap these callables with that API here.
    """

    def _tool_wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    _tool_wrapper.__name__ = name
    _tool_wrapper.__doc__ = f"Modell tool: {name}"
    return _tool_wrapper
