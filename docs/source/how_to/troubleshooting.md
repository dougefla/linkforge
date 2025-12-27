# Troubleshooting

This guide provides solutions to common issues encountered when building, validating, or exporting robots with LinkForge.

## Simulation Issues

### Robot "folds" or "explodes" in Gazebo
**Symptoms**: The robot spins uncontrollably or collapses upon spawning.
**Solution**: 
- Check your **Joint Axes**. If a joint axis is misaligned with the visual orientation, the physics engine will apply forces in the wrong direction.
- Verify **Inertial Values**. Tiny or zero inertia values (`ixx`, `iyy`, `izz`) cause numerical instability. Keep the **Auto-Calculate Inertia** checkbox enabled in the LinkForge panel.

### Joints are not moving
**Symptoms**: The robot is stiff, and ROS 2 commands have no effect.
**Solution**:
- Ensure you have added a **Transmission** to the joint.
- Check that the **Hardware Interface** (position, velocity, effort) matches what your controller expects.

## Blender-Specific Modeling Issues

### Object vs. Mesh Data confusion
**Symptoms**: You change the mass of one link, and all other identical links change too.
**Solution**: 
- LinkForge stores some properties at the **Mesh Data** level to allow for efficient XACRO macro generation.
- If you need a link to have unique mass/inertia while sharing geometry, make the mesh data single-user in Blender (`Object > Relations > Make Single User > Object & Data`).

### Floating/Disconnected Links
**Symptoms**: The robot collapses or parts of it don't move with the rest.
**Solution**:
- Use the **LinkForge Validation** panel. It will highlight links that aren't part of the main kinematic tree.
- Ensure every link (except the root) has a parent joint connecting it to another link.

### "Inverted" Joints
**Symptoms**: A revolute joint rotates in the opposite direction of your command.
**Solution**:
- Select the joint in Blender and look for the **Joint Axis** visual arrow.
- Flip the axis in the Joint Panel or rotate the joint's local coordinate system in Blender.

## Export & Import Issues

### Mesh path not found
**Symptoms**: The robot appears invisible or has broken geometry in Gazebo.
**Solution**:
- LinkForge uses repository-relative paths (e.g., `package://robot_description/meshes/`). 
- Ensure your `package.xml` and folder structure match the export path settings in the **Validate & Export** tab.

### "No Root Link Found" Error
**Symptoms**: Validation fails with a root link error.
**Solution**:
- Every robot must have exactly one link that is not a child of any joint. 
- Use the **Validation** panel to identify the disconnected "island" of links.

## UI & Viewport Issues

### Joint axes are too big/small
**Symptoms**: The viewport is cluttered with giant axis arrows.
**Solution**:
- Go to **Blender Preferences > Add-ons > LinkForge**.
- Adjust the **Joint Visualization Size** slider to your preference.
