"""Operators for driving robot joints interactively."""

from __future__ import annotations

import contextlib
import typing

import bpy

from ..properties.joint_props import _capture_rest_state
from ..utils.decorators import OperatorReturn, safe_execute

if typing.TYPE_CHECKING:
    from bpy.types import Context, Operator

    from ..properties.joint_props import JointPropertyGroup
else:
    Context = typing.Any
    Operator = getattr(getattr(bpy, "types", object), "Operator", object)


def _iter_robot_joints(context: Context) -> typing.Iterator[tuple[bpy.types.Object, typing.Any]]:
    """Yield (object, joint_props) for every robot joint in the scene."""
    scene = context.scene
    if not scene:
        return
    for obj in scene.objects:
        if obj.type != "EMPTY":
            continue
        props = getattr(obj, "linkforge_joint", None)
        if props and props.is_robot_joint:
            yield obj, props


class LINKFORGE_OT_reset_all_joints(Operator):
    """Reset all robot joints to their zero (rest) position."""

    bl_idname = "linkforge.reset_all_joints"
    bl_label = "Reset All Joints"
    bl_description = "Set all joint positions back to zero"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Check if operator can run."""
        scene = context.scene
        if not scene:
            return False
        for obj in scene.objects:
            if (
                obj.type == "EMPTY"
                and hasattr(obj, "linkforge_joint")
                and typing.cast("JointPropertyGroup", getattr(obj, "linkforge_joint")).is_robot_joint
            ):
                return True
        return False

    @safe_execute
    def execute(self, context: Context) -> OperatorReturn:
        """Execute the operator."""
        count = 0
        for _obj, props in _iter_robot_joints(context):
            if props.joint_position != 0.0:
                props.joint_position = 0.0
                count += 1
        self.report({"INFO"}, f"Reset {count} joint(s) to zero")
        return {"FINISHED"}


class LINKFORGE_OT_capture_rest_pose(Operator):
    """Capture the current transform of all joints as the rest (zero) pose."""

    bl_idname = "linkforge.capture_rest_pose"
    bl_label = "Capture Rest Pose"
    bl_description = "Store current transforms as the zero-position reference for all joints"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Check if operator can run."""
        scene = context.scene
        if not scene:
            return False
        for obj in scene.objects:
            if (
                obj.type == "EMPTY"
                and hasattr(obj, "linkforge_joint")
                and typing.cast("JointPropertyGroup", getattr(obj, "linkforge_joint")).is_robot_joint
            ):
                return True
        return False

    @safe_execute
    def execute(self, context: Context) -> OperatorReturn:
        """Execute the operator."""
        count = 0
        for obj, props in _iter_robot_joints(context):
            props.joint_position = 0.0
            _capture_rest_state(props, obj)
            count += 1
        self.report({"INFO"}, f"Captured rest pose for {count} joint(s)")
        return {"FINISHED"}


# Registration
classes = [
    LINKFORGE_OT_reset_all_joints,
    LINKFORGE_OT_capture_rest_pose,
]


def register() -> None:
    """Register operators."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister operators."""
    for cls in reversed(classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
