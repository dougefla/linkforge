# Troubleshooting

This guide provides solutions to common issues encountered when building, validating, or exporting robots with LinkForge.

## Simulation Issues

### Robot "folds" or "explodes" in Gazebo
**Symptoms**: The robot spins uncontrollably or collapses upon spawning.
**Solution**: 
- Check your **Joint Axes**. If a joint axis is misaligned with the visual orientation, the physics engine will apply forces in the wrong direction.
- Verify **Inertial Values**. Tiny or zero inertia values (`ixx`, `iyy`, `izz`) cause numerical instability. Use the **Calculate Inertia** button in the LinkForge panel.

### Joints are not moving
**Symptoms**: The robot is stiff, and ROS 2 commands have no effect.
**Solution**:
- Ensure you have added a **Transmission** to the joint.
- Check that the **Hardware Interface** (position, velocity, effort) matches what your controller expects.

## Export & Import Issues

### Mesh path not found
**Symptoms**: The robot appears invisible or has broken geometry in Gazebo.
**Solution**:
- LinkForge uses repository-relative paths (e.g., `package://robot_description/meshes/`). 
- Ensure your `package.xml` and folder structure match the export path settings in the Export tab.

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
