# How-to: Manage Collision Geometry

Collision geometry defines the physical shape of your robot used by physics engines (like ODE or Bullet) to calculate contacts, friction, and collisions.

## 1. Why Collision Matters
While your **Visual** meshes can be high-poly and complex for aesthetics, **Collision** meshes should be as simple as possible (primitives or convex hulls) to ensure simulation performance and stability.

## 2. Generating Collisions
LinkForge makes it easy to generate optimized collision geometry from your visuals:

1. Select a **Link** (the Empty object) or any of its children.
2. Go to the **Link** tab in the LinkForge panel.
3. Click **Generate Collision**.

### Collision Types
In the settings below the button, you can choose the generation strategy:
- **Auto-Detect**: LinkForge analyzes the visual mesh. If it resembles a cube, sphere, or cylinder, it creates a corresponding primitive. Otherwise, it generates a **Convex Hull**.
- **Box/Sphere/Cylinder**: Force LinkForge to use a specific primitive shape based on the visual's bounding box.
- **Convex Hull**: Shrink-wraps the visual mesh. Best for complex, non-primitive parts.

## 3. Compound Collisions
If a Link has multiple visual meshes (e.g., a chassis made of several separate parts), LinkForge will automatically merge them into a **single compound collision hull** when you click Generate Collision. This follows industry best practices for simulation stability.

## 4. Live Preview & Quality
- **Collision Quality**: Use the slider to decimate the generated convex hull. Lower quality means fewer vertices and faster simulation.
- **Toggling Visibility**: Collisions are hidden by default to keep the viewport clean. Click the **Show/Hide Collision** button in the **Link** tab or use the **Show Collisions** toggle (with the wireframe icon) in the **Validate & Export** tab to inspect your collision meshes.

## 5. Manual Collisions
If you want to provide your own hand-optimized collision mesh:
1. Create or select a mesh to use as your collision.
2. **Parent the mesh** to your Link object (it must appear as a child in the Blender Outliner).
3. Ensure the mesh name ends with the `_collision` suffix (e.g., `chassis_collision`).
4. LinkForge will automatically detect this and use it instead of generating one.
