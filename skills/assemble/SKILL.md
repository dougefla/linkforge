---
name: assemble
description: "Assemble articulated furniture from OBJ mesh parts into URDF using Blender MCP and LinkForge. Use when asked to convert OBJ files to URDF, assemble furniture, or build articulated models from mesh parts."
user-invocable: true
argument-hint: "[obj_directory] [object_type?] [output_directory?]"
---

# Assemble Articulated Furniture from OBJ to URDF

You are an expert robotics engineer assembling articulated furniture objects from separate .obj mesh parts into a complete URDF model. You use Blender via MCP tools and the LinkForge plugin.

## Arguments

- `$1` (required): Path to directory containing .obj/.mtl files (one per part)
- `$2` (optional): Object type hint (e.g., "cabinet", "desk", "wardrobe"). If omitted, infer from visual analysis.
- `$3` (optional): Output directory for URDF + meshes. Defaults to `$1/urdf_output/`.

## Prerequisites

- Blender must be running with LinkForge plugin enabled
- BlenderMCP server must be started (port 9876)
- The MCP tools `mcp__blender__execute_blender_code` and `mcp__blender__get_viewport_screenshot` must be available

## Workflow Overview

Execute these 5 phases sequentially. Each phase uses MCP tools to interact with Blender. Break Blender code into small focused calls (one logical step per call). Analyze screenshots between steps to make decisions.

---

## Phase 1: Import & Visual Analysis

### Step 1.1: Clear Scene

```python
import bpy
# Delete all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)
# Delete orphan data
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)
for mat in bpy.data.materials:
    bpy.data.materials.remove(mat)
print("Scene cleared")
```

### Step 1.2: Import OBJ Files

```python
import bpy
from pathlib import Path

obj_dir = Path("$1")  # replace with actual path
obj_files = sorted(obj_dir.glob("*.obj"))
imported = []

for obj_path in obj_files:
    before = set(o.name for o in bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(obj_path))
    after = set(o.name for o in bpy.data.objects)
    new_objs = after - before
    part_name = obj_path.stem
    # Rename and track
    for name in new_objs:
        obj = bpy.data.objects[name]
        if obj.type == 'MESH':
            obj.name = part_name
            imported.append(part_name)

print(f"Imported {len(imported)} parts: {imported}")
```

If a single OBJ imports as multiple objects, join them:
```python
import bpy
# Select all objects from one OBJ, join into one
bpy.ops.object.select_all(action='DESELECT')
for obj in objects_to_join:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects_to_join[0]
bpy.ops.object.join()
```

### Step 1.3: Gather Geometry Data

```python
import bpy, json
from mathutils import Vector

parts = []
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    d = obj.dimensions
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    bb_min = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    bb_max = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    vol = d.x * d.y * d.z
    min_dim = min(d.x, d.y, d.z)
    max_dim = max(d.x, d.y, d.z)
    parts.append({
        'name': obj.name,
        'dimensions': [round(d.x,4), round(d.y,4), round(d.z,4)],
        'volume': round(vol, 6),
        'flatness': round(min_dim / max_dim, 3) if max_dim > 0 else 0,
        'location': [round(obj.location.x,4), round(obj.location.y,4), round(obj.location.z,4)],
        'bb_min': [round(bb_min.x,4), round(bb_min.y,4), round(bb_min.z,4)],
        'bb_max': [round(bb_max.x,4), round(bb_max.y,4), round(bb_max.z,4)],
        'vertex_count': len(obj.data.vertices),
    })

parts.sort(key=lambda p: p['volume'], reverse=True)
print(json.dumps(parts, indent=2))
```

### Step 1.4: Multi-Angle Screenshots

Position the 3D viewport to frame all objects, then take screenshots from 4 angles. Use `mcp__blender__get_viewport_screenshot` after each camera repositioning.

```python
import bpy
from mathutils import Quaternion
from math import radians

# Frame all objects
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for region in area.regions:
            if region.type == 'WINDOW':
                with bpy.context.temp_override(area=area, region=region):
                    bpy.ops.view3d.view_all()
        # Set perspective view
        area.spaces[0].region_3d.view_perspective = 'PERSP'
```

Take screenshot with `mcp__blender__get_viewport_screenshot`, then analyze the image.

**Visual Analysis**: Look at the screenshots and determine:
1. What type of furniture is this? (cabinet, desk, wardrobe, shelf unit, etc.)
2. How many distinct parts are visible?
3. Which parts appear movable? (doors, drawers, lids)
4. What is the general orientation? (which way is "front"?)

---

## Phase 2: Part Classification

Using the geometry data from Step 1.3 and the visual analysis from Step 1.4, classify each part.

### Classification Decision Tree

For each part, evaluate in order:

1. **Is it the largest part by volume?** → Candidate for **body/base** (root link)
2. **Is it very small (volume < 5% of body)?** → **Handle/knob** (fixed joint to nearest door/drawer)
3. **Is it flat (flatness < 0.15) AND vertical (Z extent > X or Y extent)?** → **Door** (revolute joint)
4. **Is it flat (flatness < 0.15) AND horizontal (Z extent is the smallest)?** →
   - If near the top of body → **Lid/flap** (revolute joint, X or Y axis)
   - If inside body → **Shelf** (fixed joint)
5. **Is it box-shaped (flatness > 0.3) AND inside the body?** → **Drawer** (prismatic joint)
6. **Otherwise** → **Fixed component** (fixed joint to body)

### Output Format

Construct a classification table:

| Part Name | Role | Parent | Joint Type | Joint Axis | Est. Limits |
|-----------|------|--------|------------|------------|-------------|
| body      | base | (root) | -          | -          | -           |
| door_left | door | body   | REVOLUTE   | Z          | [0, pi/2]   |
| drawer_1  | drawer | body | PRISMATIC  | Y          | [0, 0.4]    |
| shelf_1   | shelf | body  | FIXED      | -          | -           |
| handle_1  | handle | door_left | FIXED  | -          | -           |

---

## Phase 3: Assembly

### Step 3.1: Set Robot Name

```python
import bpy
bpy.context.scene.linkforge.robot_name = "furniture_cabinet"  # from Phase 1 analysis
```

### Step 3.2: Create Links

For each part, create a LinkForge link. Execute for each part:

```python
import bpy

mesh_obj = bpy.data.objects["PART_NAME"]  # the imported mesh
link_name = "PART_NAME"

# Rename mesh to visual convention
mesh_obj.name = f"{link_name}_visual"

# Create Empty as link frame
empty = bpy.data.objects.new(link_name, None)
empty.empty_display_type = "PLAIN_AXES"
empty.empty_display_size = 0.05
empty.rotation_mode = "XYZ"
bpy.context.scene.collection.objects.link(empty)

# Position at mesh center
empty.location = mesh_obj.location.copy()
empty.rotation_euler = mesh_obj.rotation_euler.copy()

# Parent mesh to link Empty
mesh_obj.parent = empty
mesh_obj.matrix_parent_inverse = empty.matrix_world.inverted()

# Mark as robot link
empty.linkforge.is_robot_link = True
empty.linkforge.link_name = link_name

# Estimate mass from volume (total ~20kg, proportional to volume)
empty.linkforge.mass = ESTIMATED_MASS  # compute from volume ratio
empty.linkforge.use_auto_inertia = True

bpy.context.view_layer.update()
```

### Step 3.3: Determine Joint Origins

#### For Doors (Revolute)

Find the hinge edge — the vertical edge of the door closest to the body:

```python
import bpy
from mathutils import Vector

door_visual = bpy.data.objects["door_left_visual"]
body_visual = bpy.data.objects["body_visual"]

# World bounding boxes
door_bb = [door_visual.matrix_world @ Vector(c) for c in door_visual.bound_box]
body_bb = [body_visual.matrix_world @ Vector(c) for c in body_visual.bound_box]

door_min_x = min(v.x for v in door_bb)
door_max_x = max(v.x for v in door_bb)
door_min_z = min(v.z for v in door_bb)
door_max_z = max(v.z for v in door_bb)

body_min_x = min(v.x for v in body_bb)
body_max_x = max(v.x for v in body_bb)

# Determine hinge side
left_dist = abs(door_min_x - body_min_x)
right_dist = abs(door_max_x - body_max_x)

if left_dist < right_dist:
    hinge_x = door_min_x  # hinge on left
else:
    hinge_x = door_max_x  # hinge on right

hinge_y = min(v.y for v in door_bb)  # front face
hinge_z = (door_min_z + door_max_z) / 2  # vertical center

print(f"Hinge at: ({hinge_x}, {hinge_y}, {hinge_z})")
```

#### For Drawers (Prismatic)

The joint origin is at the drawer's rest position. The axis is typically along the direction the drawer slides out (usually -Y for front-facing furniture, meaning the drawer moves toward the viewer):

```python
drawer_visual = bpy.data.objects["drawer_1_visual"]
d_bb = [drawer_visual.matrix_world @ Vector(c) for c in drawer_visual.bound_box]
drawer_depth = max(v.y for v in d_bb) - min(v.y for v in d_bb)
# Joint limit: 0 to drawer_depth (or slightly less)
print(f"Drawer depth: {drawer_depth}, prismatic limit: [0, {drawer_depth * 0.9}]")
```

### Step 3.4: Create Joints

For each non-root part, create a joint:

```python
import bpy

# Create joint Empty
joint_obj = bpy.data.objects.new("JOINT_NAME", None)
joint_obj.empty_display_type = "ARROWS"
joint_obj.empty_display_size = 0.1
joint_obj.rotation_mode = "XYZ"
bpy.context.scene.collection.objects.link(joint_obj)

# Position at computed joint origin
joint_obj.location = (HINGE_X, HINGE_Y, HINGE_Z)

# Set joint properties
jp = joint_obj.linkforge_joint
jp.is_robot_joint = True
jp.joint_name = "JOINT_NAME"
jp.joint_type = "REVOLUTE"  # or "PRISMATIC" or "FIXED"
jp.axis = "Z"               # or "X", "Y"
jp.use_limits = True
jp.limit_lower = 0.0
jp.limit_upper = 1.5708     # pi/2 for 90-degree door
jp.limit_effort = 10.0
jp.limit_velocity = 1.0

# Connect parent and child
jp.parent_link = bpy.data.objects["body"]       # link Empty
jp.child_link = bpy.data.objects["door_left"]   # link Empty

# Establish Blender hierarchy
joint_obj.parent = bpy.data.objects["body"]
joint_obj.matrix_parent_inverse = bpy.data.objects["body"].matrix_world.inverted()

child_link = bpy.data.objects["door_left"]
child_link.parent = joint_obj
child_link.matrix_parent_inverse = joint_obj.matrix_world.inverted()

bpy.context.view_layer.update()
```

### Step 3.5: Capture Rest State

After creating ALL joints:

```python
import bpy
from linkforge.blender.properties.joint_props import _capture_rest_state

for obj in bpy.context.scene.objects:
    if obj.type == 'EMPTY' and hasattr(obj, 'linkforge_joint') and obj.linkforge_joint.is_robot_joint:
        _capture_rest_state(obj.linkforge_joint, obj)

print("Rest state captured for all joints")
```

### Joint Axis Quick Reference (Furniture)

| Part Type | Joint Type | Typical Axis | Typical Limits |
|-----------|-----------|-------------|---------------|
| Side-hinged door | REVOLUTE | Z | [0, pi/2] or [-pi/2, 0] |
| Double door (left) | REVOLUTE | Z | [0, pi/2] |
| Double door (right) | REVOLUTE | Z | [-pi/2, 0] |
| Top-hinged flap | REVOLUTE | X | [0, pi/2] |
| Bottom-hinged flap | REVOLUTE | X | [-pi/2, 0] |
| Drawer | PRISMATIC | Y (negative = pull out) | [0, depth*0.9] |
| Shelf | FIXED | - | - |
| Handle | FIXED | - | - |

### Mass Estimation

Distribute a total estimated furniture mass proportionally by volume:
```
total_mass = 20.0  # kg, typical for medium cabinet
part_mass = total_mass * (part_volume / total_volume)
part_mass = max(part_mass, 0.1)  # minimum 100g
```

---

## Phase 4: Validation

### Step 4.1: Drive Each Joint and Screenshot

For each moveable joint, drive through 5 positions and take a screenshot at each:

```python
import bpy

joint_obj = bpy.data.objects["JOINT_NAME"]
jp = joint_obj.linkforge_joint
lower = jp.limit_lower
upper = jp.limit_upper

for pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
    pos = lower + pct * (upper - lower)
    jp.joint_position = pos
    bpy.context.view_layer.update()
    print(f"Joint at {pct*100}%: position = {pos:.3f}")
```

After setting each position, call `mcp__blender__get_viewport_screenshot` and analyze the image for:

### Visual Check Criteria

1. **Interpenetration**: Any part passing through another part? Look for overlapping geometry.
2. **Gaps**: Are parts that should be flush showing visible separation?
3. **Wrong Axis**: Does the movement direction look correct? A door should swing, not slide.
4. **Wrong Limits**: Does the joint move too far (door goes through body) or not far enough?
5. **Wrong Hinge Point**: Does the door rotate around the correct edge?

### Step 4.2: Bounding Box Overlap Check

Automated geometric check at extreme positions:

```python
import bpy
from mathutils import Vector

def get_world_bbox(obj):
    """Get world-space AABB for a mesh object."""
    if obj.type != 'MESH':
        return None, None
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    bb_min = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    bb_max = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    return bb_min, bb_max

def aabb_overlap(a_min, a_max, b_min, b_max):
    """Check if two AABBs overlap."""
    return all(a_min[i] < b_max[i] and a_max[i] > b_min[i] for i in range(3))

# Check each moveable part against body at 100% position
body_min, body_max = get_world_bbox(bpy.data.objects.get("body_visual"))
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and '_visual' in obj.name and 'body' not in obj.name:
        p_min, p_max = get_world_bbox(obj)
        if p_min and body_min and aabb_overlap(p_min, p_max, body_min, body_max):
            print(f"WARNING: {obj.name} overlaps with body at current position!")
```

### Step 4.3: Iterative Correction

If issues are found:
1. Identify the problem (which joint, what issue)
2. Adjust the specific parameter:
   - Wrong axis → change `jp.axis`
   - Wrong hinge → reposition joint Empty
   - Wrong limits → adjust `jp.limit_lower` / `jp.limit_upper`
   - Interpenetration → reduce limits or adjust origin
3. Recapture rest state if joint was repositioned
4. Re-validate that specific joint
5. Maximum 3 correction rounds per joint

### Step 4.4: Reset After Validation

```python
import bpy
bpy.ops.linkforge.reset_all_joints()
print("All joints reset to rest pose")
```

---

## Phase 5: Export

### Step 5.1: Export URDF

```python
import bpy
from pathlib import Path

output_dir = Path("OUTPUT_DIR")  # replace with $3 or $1/urdf_output
urdf_path = output_dir / "furniture.urdf"
meshes_dir = output_dir / "meshes"
meshes_dir.mkdir(parents=True, exist_ok=True)

# Set export properties
scene = bpy.context.scene
scene.linkforge.export_format = "URDF"
scene.linkforge.export_meshes = True
scene.linkforge.mesh_format = "OBJ"

# Convert and export
from linkforge.blender.adapters.blender_to_core import scene_to_robot
from linkforge_core.generators.urdf_generator import URDFGenerator

robot, errors = scene_to_robot(bpy.context, meshes_dir=meshes_dir, dry_run=False)

if errors:
    print(f"Warnings: {errors}")

generator = URDFGenerator(pretty_print=True, urdf_path=urdf_path)
generator.write(robot, urdf_path, validate=False)

print(f"Exported: {urdf_path}")
print(f"Links: {len(robot.links)}, Joints: {len(robot.joints)}")
for j in robot.joints:
    print(f"  {j.name}: {j.type.name} ({j.parent} -> {j.child})")
```

### Step 5.2: Final Summary

Report to the user:
- Furniture type identified
- Number of links and joints
- Degrees of freedom
- Joint details table (name, type, axis, limits)
- Output file paths (URDF, mesh directory)
- Any warnings from validation

---

## Edge Cases

1. **Single OBJ file**: Create a single-link URDF with no joints.
2. **No clear body**: Use the largest part. If ambiguous, ask the user.
3. **Multiple objects from one OBJ**: Join them with `bpy.ops.object.join()`.
4. **Scale issues**: Check if dimensions are reasonable (furniture should be 0.3m-3m). If not, scale uniformly.
5. **Handles on doors**: Detect by proximity — attach to nearest door/drawer link, not body.
6. **Symmetric double doors**: Each door gets its own revolute joint. Left hinge on left, right hinge on right. Limits are mirrored.

---

## Important API Notes

- Link property group: `obj.linkforge` (NOT `obj.linkforge_link`)
- Joint property group: `obj.linkforge_joint`
- `joint_type` values: `"REVOLUTE"`, `"CONTINUOUS"`, `"PRISMATIC"`, `"FIXED"`, `"FLOATING"`, `"PLANAR"`
- `axis` values: `"X"`, `"Y"`, `"Z"`, `"CUSTOM"`
- `parent_link` and `child_link` are PointerProperty — assign Blender Object references, not strings
- Always call `bpy.context.view_layer.update()` after hierarchy changes
- Always use `matrix_parent_inverse = parent.matrix_world.inverted()` after setting parent
- Visual meshes must be named `*_visual`, collision meshes `*_collision`
