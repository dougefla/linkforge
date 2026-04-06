# /assemble Skill — Furniture OBJ to URDF Assembly

Automatically assemble articulated furniture from separate .obj mesh parts into a complete URDF model using Blender, LinkForge, and Claude Code.

## Prerequisites

1. **Blender 4.2+** with the [LinkForge](https://github.com/dougefla/linkforge) extension installed
2. **BlenderMCP** addon running in Blender (provides MCP socket server)
3. **Claude Code** with MCP configured to connect to BlenderMCP

### Install LinkForge

```bash
cd /path/to/linkforge
uv run python platforms/blender/scripts/build.py build
# Then in Blender: Edit > Preferences > Get Extensions > Install from Disk
# Select: dist/linkforge-blender-*.zip
```

### Install BlenderMCP

Follow the instructions at [blender-mcp](https://github.com/dougefla/blender-mcp). Ensure the MCP server is configured in your Claude Code settings:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

## Install the Skill

```bash
# From the linkforge repository root
ln -sf "$(pwd)/skills/assemble" ~/.claude/skills/assemble
```

Verify:
```bash
ls -la ~/.claude/skills/assemble/SKILL.md
```

## Usage

Start the BlenderMCP server in Blender (sidebar > BlenderMCP > Start MCP Server), then in Claude Code:

```
/assemble /path/to/furniture/obj_parts
```

### With optional arguments

```
/assemble /path/to/obj_parts cabinet /path/to/output
```

- Argument 1: Directory containing .obj/.mtl files (required)
- Argument 2: Object type hint — "cabinet", "desk", "wardrobe" (optional, auto-detected if omitted)
- Argument 3: Output directory for URDF + meshes (optional, defaults to `<obj_dir>/urdf_output/`)

## Input Format

The input directory should contain one .obj file per part:

```
furniture_parts/
  body.obj
  body.mtl
  door_left.obj
  door_left.mtl
  door_right.obj
  door_right.mtl
  drawer.obj
  drawer.mtl
  shelf.obj
  shelf.mtl
```

## Output

```
urdf_output/
  furniture.urdf
  meshes/
    body_visual.obj
    door_left_visual.obj
    ...
```

## What It Does

1. **Import** all .obj parts into Blender
2. **Analyze** the model visually (screenshots + geometry) to determine furniture type
3. **Classify** each part (body, door, drawer, shelf, handle, etc.)
4. **Assemble** with LinkForge: create links, joints, set axes and limits
5. **Validate** by driving joints and checking for interpenetration/gaps
6. **Export** to URDF with mesh files

## Uninstall

```bash
rm ~/.claude/skills/assemble
```
