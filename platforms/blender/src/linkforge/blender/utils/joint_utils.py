"""Kinematics utilities for the Blender platform."""

from __future__ import annotations

import typing

import bpy
from bpy.types import Context
from linkforge.core import Joint

from ..constants import PROP_JOINT
from .property_helpers import find_property_owner, get_joint_props

if typing.TYPE_CHECKING:
    from ..properties.joint_props import JointPropertyGroup


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


def _resolve_axis_vector(props: JointPropertyGroup) -> typing.Any:
    """Return the joint axis as a unit Vector in the joint's local frame."""
    from mathutils import Vector

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
    if axis.length > 1e-9:
        return axis.normalized()
    return Vector((0.0, 0.0, 1.0))


def apply_joint_state(props: JointPropertyGroup, context: Context) -> None:
    """Apply ``props.joint_state`` to the child link's local transform.

    Revolute/continuous joints rotate the child link about the joint axis.
    Prismatic joints translate the child link along the joint axis. All
    other joint types are no-ops. The displacement is expressed relative to
    the joint Empty, so the URDF rest origin (baked into the joint Empty's
    location/rotation) is preserved.

    Revolute and prismatic joint_state values are clamped to
    ``[limit_lower, limit_upper]``. Continuous joints accept any angle.
    """
    from mathutils import Quaternion

    if not props.is_robot_joint:
        return

    joint_obj = find_property_owner(context, props, PROP_JOINT)
    if joint_obj is None:
        return

    child = props.child_link
    if child is None:
        return

    state = float(props.joint_state)

    # Clamp to hard limits for joint types that require them
    if props.joint_type in {"REVOLUTE", "PRISMATIC"}:
        lower = float(props.limit_lower)
        upper = float(props.limit_upper)
        if lower > upper:
            lower, upper = upper, lower
        clamped = max(lower, min(upper, state))
        if clamped != state:
            # Write back through the ID-property dict to avoid re-entering
            # the update callback (which would otherwise loop).
            props["joint_state"] = clamped
            state = clamped

    if props.joint_type in {"REVOLUTE", "CONTINUOUS"}:
        child.rotation_mode = "XYZ"
        if props.axis == "X":
            child.rotation_euler = (state, 0.0, 0.0)
        elif props.axis == "Y":
            child.rotation_euler = (0.0, state, 0.0)
        elif props.axis == "Z":
            child.rotation_euler = (0.0, 0.0, state)
        else:  # CUSTOM — build the rotation from axis-angle via quaternion
            import math

            axis = _resolve_axis_vector(props)
            half = state * 0.5
            s = math.sin(half)
            quat = Quaternion((math.cos(half), axis.x * s, axis.y * s, axis.z * s))
            child.rotation_euler = quat.to_euler("XYZ")
        child.location = (0.0, 0.0, 0.0)
    elif props.joint_type == "PRISMATIC":
        axis = _resolve_axis_vector(props)
        child.location = (axis.x * state, axis.y * state, axis.z * state)
        child.rotation_mode = "XYZ"
        child.rotation_euler = (0.0, 0.0, 0.0)
    # FIXED/FLOATING/PLANAR: no single-DOF state to apply
