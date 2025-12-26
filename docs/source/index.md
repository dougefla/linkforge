# LinkForge Documentation

Welcome to the official LinkForge documentation. LinkForge is a professional Blender extension designed to bridge the gap between 3D modeling and robotics simulation.

Following the **Diátaxis framework**, our documentation is organized into four sections to help you find exactly what you need.

## 🔄 Workflow at a Glance

```mermaid
graph LR
    A[3D Modeling in Blender] --> B[LinkForge: Setup Robot]
    B --> C{Validation}
    C -- Errors --> B
    C -- Success --> D[Export URDF/XACRO]
    D --> E[ROS 2 / Gazebo Simulation]
```

---

::::{grid} 2
:gutter: 3

:::{grid-item-card} 🚀 Tutorials
:link: tutorials/index
:link-type: doc

**Learning-oriented.** Start here if you are new to LinkForge. Step-by-step lessons to build your first robot.
^^^
- [Building a Diff-Drive Robot](tutorials/building_diff_drive)
:::

:::{grid-item-card} 🛠️ How-to Guides
:link: how_to/index
:link-type: doc

**Task-oriented.** Practical guides to help you achieve specific goals or solve problems.
^^^
- [Adding Sensors](how_to/add_sensors)
- [Defining Joints](how_to/index)
:::

:::{grid-item-card} 💡 Explanation
:link: explanation/index
:link-type: doc

**Understanding-oriented.** Deep dives into the architecture, theory, and design of LinkForge.
^^^
- [Architecture Guide](explanation/ARCHITECTURE)
- [Data Model](explanation/data_model)
:::

:::{grid-item-card} 📚 Reference
:link: reference/index
:link-type: doc

**Information-oriented.** Technical descriptions, API documentation, and specifications.
^^^
- [Python API Reference](reference/api/index)
- [URDF Specification](reference/index)
:::

::::

---

```{toctree}
:maxdepth: 2
:hidden:
:caption: Tutorials

tutorials/index
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: How-to Guides

how_to/index
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Explanation

explanation/index
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Reference

reference/index
CHANGELOG
CONTRIBUTING
README
LICENSE
```

## Quick Links

- [GitHub Repository](https://github.com/arounamounchili/linkforge)
- [Issue Tracker](https://github.com/arounamounchili/linkforge/issues)
- [Discussions](https://github.com/arounamounchili/linkforge/discussions)
