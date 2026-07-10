
The goal of this project is to be able to play Quake2 using OpenGL written in Python.

To do that we convert Quake2 written in C to Python.

Here is the original C source code:

C:\BackupNo\Coding\Projects\Quake-2

Single Player is the first big milestone. Multiplayer is not important at the moment.

Focus only on the opengl driver, use a good open gl lib for python.

Dont convert the software renderer.

Quake2 game resources: D:\SteamLibrary\steamapps\common\Quake 2

Here are all the game resources unpacked: C:\Action\id\q2unpacked

NEXT:

this renderer’s particle draw path is still stubbed, implement it

every monster fires generic blaster bolts rather than its specific weapon. fix that.

Add the HUD

Add menus

Saving / Loading

Implement moving platforms, like lifts.


Make Enemies take damage, play death animation, make enemies attack player.

The grenade launcher shall fire a greade that shows the explosion model when the grenade explodes.

LATER:

Network protocol (cl_parse.py) for multiplayer support





IMPORTANT - pitch angle convention:

This engine's pitch sign is MIRRORED from the original Quake 2 C code:
positive pitch looks UP here (in original Quake 2, positive pitch looks down).
The camera view matrix (_make_view_matrix in ref_gl/gl_rmain.py) and the mouse
handling in quake2/cl_input.py define this convention.

So when porting any C code that uses AngleVectors or vectoangles, flip the
pitch sign: forward.z = +sin(pitch) instead of -sin(pitch), and
pitch = +atan2(z, horizontal) instead of negated. See _angle_vectors and
_vector_to_angles in quake2/cl_weapon.py for the correct reference versions.
