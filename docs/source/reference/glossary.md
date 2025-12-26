# Glossary

This glossary defines key terms used throughout the LinkForge documentation, Blender integration, and URDF/XACRO standards.

## Link
A representation of a rigid body in a robot model. Every link must have a unique name. Links contain properties for **Visual**, **Collision**, and **Inertial** data.

## Joint
A connection between two links that defines their relative motion (e.g., revolute, prismatic, fixed, continuous).

## Root Link
The base of the robot's kinematic tree. A robot can only have one root link, and it must not have any parent joint.

## Inertia Tensor
A 3x3 matrix representing the rotational inertia of a rigid body. LinkForge simplifies this by calculating the moments of inertia (`ixx`, `iyy`, `izz`) based on the object's geometry and mass.

## Transmission
A mechanism that links an actuator (motor) to a joint. In ROS 2, transmissions define the hardware interface (e.g., position, velocity, or effort).

## URDF (Unified Robot Description Format)
An XML format used in ROS to describe the physical properties of a robot.

## XACRO (XML Macros)
An XML macro language used to simplify URDF files by allowing variables, math, and macros.

## Actuation Vector
The visual representation in Blender showing the direction of force or movement for a specific joint transmission.
