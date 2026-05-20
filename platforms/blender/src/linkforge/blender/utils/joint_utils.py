"""Kinematics utilities for the Blender platform."""

from __future__ import annotations

import math
import typing

import bpy
from bpy.types import Context
from linkforge.core import Joint
from mathutils import Quaternion, Vector

from .property_helpers import get_joint_props

if typing.TYPE_CHECKING:
    from ..properties.joint_props import JointPropertyGroup


# Joint-state writes must be cheap: the slider fires this on every mouse-move
# tick. Touch a property only when its value actually changes — each assignment
# dirties the depsgraph and (because the child link is in the depsgraph_update
# handler) walks all robot-link sync logic.
_ZERO3 = (0.0, 0.0, 0.0)
_EPS = 1e-9
_DOF_TYPES = frozenset({"revolute", "continuous", "prismatic"})
_LIMITED_TYPES = frozenset({"revolute", "prismatic"})
_ROTATIONAL_TYPES = frozenset({"revolute", "continuous"})


def resolve_mimic_joints(joints: list[Joint], joint_objects: dict[str, bpy.types.Object]) -> None:
    """Resolve mimic joint pointers after all joint objects have been created.

    Args:
        joints: List of joint models
        joint_objects: Dictionary mapping joint names to Blender objects
    """
    for joint in joints:
        if joint.mimic and joint.name in joint_objects:
            joint_obj = joint_objects[joint.name]
            if jp := get_joint_props(joint_obj):
                # Use joint_objects map to find the mimic target object
                if joint.mimic.joint in joint_objects:
                    mimic_target_obj = joint_objects[joint.mimic.joint]
                    jp.mimic_joint = mimic_target_obj
                    jp.use_mimic = True
                jp.mimic_multiplier = joint.mimic.multiplier
                jp.mimic_offset = joint.mimic.offset


def _resolve_axis_vector(props: JointPropertyGroup) -> Vector:
    """Return the joint axis as a unit Vector in the joint's local frame."""
    if props.axis == "X":
        return Vector((1.0, 0.0, 0.0))
    if props.axis == "Y":
        return Vector((0.0, 1.0, 0.0))
    if props.axis == "Z":
        return Vector((0.0, 0.0, 1.0))
    # CUSTOM (normalized; fall back to Z if degenerate)
    axis = Vector(
        (
            float(props.custom_axis_x),
            float(props.custom_axis_y),
            float(props.custom_axis_z),
        )
    )
    if axis.length > _EPS:
        return axis.normalized()
    return Vector((0.0, 0.0, 1.0))


def _set_location_if_changed(child: bpy.types.Object, new_loc: tuple[float, float, float]) -> None:
    """Assign ``child.location`` only when it differs — avoids depsgraph churn."""
    cur = child.location
    if cur[0] != new_loc[0] or cur[1] != new_loc[1] or cur[2] != new_loc[2]:
        child.location = new_loc


def _set_rotation_if_changed(
    child: bpy.types.Object, new_rot: tuple[float, float, float]
) -> None:
    """Assign ``child.rotation_euler`` only when it differs — avoids depsgraph churn."""
    cur = child.rotation_euler
    if cur[0] != new_rot[0] or cur[1] != new_rot[1] or cur[2] != new_rot[2]:
        child.rotation_euler = new_rot


def apply_joint_state(props: JointPropertyGroup, _context: Context) -> None:
    """Apply ``props.joint_state`` to the child link's local transform.

    Revolute/continuous joints rotate the child link about the joint axis.
    Prismatic joints translate the child link along the joint axis. All
    other joint types are no-ops. The displacement is expressed relative to
    the joint Empty, so the URDF rest origin (baked into the joint Empty's
    location/rotation) is preserved.

    Revolute and prismatic joint_state values are clamped to
    ``[limit_lower, limit_upper]``. Continuous joints accept any angle.
    """
    if not props.is_robot_joint:
        return

    joint_type = props.joint_type
    if joint_type not in _DOF_TYPES:
        return

    child = props.child_link
    if child is None:
        return

    state = float(props.joint_state)

    # Clamp to hard limits for joint types that require them.
    # joint_type enum identifiers are lowercase (from linkforge.core.constants).
    if joint_type in _LIMITED_TYPES:
        lower = float(props.limit_lower)
        upper = float(props.limit_upper)
        if lower > upper:
            lower, upper = upper, lower
        if state < lower:
            # Write back through the ID-property dict to avoid re-entering
            # the update callback (which would otherwise loop).
            props["joint_state"] = lower
            state = lower
        elif state > upper:
            props["joint_state"] = upper
            state = upper

    # rotation_mode is a sticky enum; only write when the child isn't already
    # set to XYZ. A redundant assignment still dirties the depsgraph.
    if child.rotation_mode != "XYZ":
        child.rotation_mode = "XYZ"

    if joint_type in _ROTATIONAL_TYPES:
        axis_name = props.axis
        if axis_name == "X":
            new_rot: tuple[float, float, float] = (state, 0.0, 0.0)
        elif axis_name == "Y":
            new_rot = (0.0, state, 0.0)
        elif axis_name == "Z":
            new_rot = (0.0, 0.0, state)
        else:  # CUSTOM — build the rotation from axis-angle via quaternion
            axis = _resolve_axis_vector(props)
            half = state * 0.5
            s = math.sin(half)
            quat = Quaternion((math.cos(half), axis.x * s, axis.y * s, axis.z * s))
            euler = quat.to_euler("XYZ")
            new_rot = (euler.x, euler.y, euler.z)
        _set_rotation_if_changed(child, new_rot)
        _set_location_if_changed(child, _ZERO3)
    else:  # prismatic
        axis_name = props.axis
        if axis_name == "X":
            new_loc: tuple[float, float, float] = (state, 0.0, 0.0)
        elif axis_name == "Y":
            new_loc = (0.0, state, 0.0)
        elif axis_name == "Z":
            new_loc = (0.0, 0.0, state)
        else:
            axis = _resolve_axis_vector(props)
            new_loc = (axis.x * state, axis.y * state, axis.z * state)
        _set_location_if_changed(child, new_loc)
        _set_rotation_if_changed(child, _ZERO3)
