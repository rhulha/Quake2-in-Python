"""
gl_rmain.py - OpenGL main renderer
Handles initialization, frame rendering, and view setup
"""

import sys
import os
import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import glFrustum as GLFrustum
from wrapper_qpy.decorators import va_args, TODO
from wrapper_qpy.custom_classes import Mutable

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ===== Global State =====

refdef = None
glstate = {
    'currenttextures': [0, 0],
    'currentmatrix': None,
}

# ===== Matrix Helpers for ModernGL =====

def _make_projection_matrix(fov_y_deg, aspect, near, far):
    """Build column-major perspective projection matrix as numpy float32."""
    f = 1.0 / math.tan(math.radians(fov_y_deg) * 0.5)
    nf = 1.0 / (near - far)
    mat = np.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) * nf, (2 * far * near) * nf],
        [0, 0, -1, 0],
    ], dtype=np.float32)
    return mat


def _make_view_matrix(vieworg, pitch_deg, yaw_deg, roll_deg):
    """Build view matrix from Quake 2 viewangles [pitch, yaw, roll]."""

    def rot_x(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=np.float32)

    def rot_y(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], dtype=np.float32)

    def rot_z(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)

    p = math.radians(-pitch_deg)
    y = math.radians(-yaw_deg)
    r = math.radians(-roll_deg)

    # Standard FPS camera: yaw around world up (Y), then pitch around local right (X)
    # No roll for first-person camera
    R = rot_x(p) @ rot_y(y)

    # Axis permutation: Quake X(forward) -> GL -Z, Q2 Y(left) -> GL -X, Q2 Z(up) -> GL Y
    perm = np.array([
        [0, -1, 0, 0],
        [0, 0, 1, 0],
        [-1, 0, 0, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)

    T = np.eye(4, dtype=np.float32)
    T[0, 3] = -vieworg[0]
    T[1, 3] = -vieworg[1]
    T[2, 3] = -vieworg[2]

    # Apply transformations: translate (in Quake space), then permute to GL space, then rotate (in GL space)
    return R @ perm @ T


# ===== Initialization =====

def R_Init():
    """Initialize OpenGL renderer"""
    try:
        from . import glw_imp, gl_image
        try:
            from quake2.common import Com_Printf, Cvar_Get
        except ImportError:
            from quake2.common import Com_Printf, Cvar_Get

        Com_Printf("R_Init()\n")

        # Create window
        if not glw_imp.GLimp_Init():
            return False

        # Get cvars
        gl_texturemode = Cvar_Get("gl_texturemode", "GL_LINEAR_MIPMAP_NEAREST", 0)
        gl_ext_swapinterval = Cvar_Get("gl_ext_swapinterval", "1", 0)

        # Verify driver
        if not glw_imp.VerifyDriver():
            return False

        # Initialize texture system
        gl_image.GL_InitImages()

        Com_Printf("R_Init complete\n")
        return True

    except Exception as e:
        print(f"R_Init error: {e}")
        return False


def R_Shutdown():
    """Shutdown renderer"""
    try:
        from . import glw_imp
        from quake2.common import Com_Printf

        Com_Printf("R_Shutdown()\n")
        glw_imp.GLimp_Shutdown()

    except Exception as e:
        print(f"R_Shutdown error: {e}")


# ===== View Setup =====

def R_SetupViewport(width, height, fov_y=75.0):
    """Setup viewport and projection matrix"""
    glViewport(0, 0, int(width), int(height))

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    aspect = width / height if height > 0 else 1.0
    near = 1.0  # Very small near plane to see close geometry
    far = 4096.0

    # Use perspective with proper FOV
    f = 1.0 / math.tan(math.radians(fov_y) / 2.0)
    GLFrustum(-near * aspect / f, near * aspect / f,
              -near / f, near / f,
              near, far)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def R_SetupMatrices(refdef):
    """Setup view matrices from refdef"""
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Get view angles from refdef (handle both list and object access)
    viewangles = refdef.viewangles if hasattr(refdef, 'viewangles') else [0, 0, 0]
    vieworg = refdef.vieworg if hasattr(refdef, 'vieworg') else [0, 0, 0]

    # Apply view rotation (pitch, yaw, roll)
    glRotatef(-viewangles[2], 1, 0, 0)  # Roll
    glRotatef(-viewangles[0], 1, 0, 0)  # Pitch
    glRotatef(-viewangles[1], 0, 1, 0)  # Yaw

    # Apply view position
    glTranslatef(-vieworg[0], -vieworg[1], -vieworg[2])


def R_ClearScreen():
    """Clear framebuffer using ModernGL"""
    try:
        from . import gl_context
        if gl_context.ctx:
            gl_context.ctx.clear(0.3, 0.3, 0.5, 1.0)
    except Exception:
        glClearColor(0.3, 0.3, 0.5, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


# ===== Rendering =====

def R_RenderFrame(refdef_in):
    """Main frame rendering function - ModernGL version"""
    global refdef

    try:
        from . import glw_imp
        from . import gl_rsurf
        from . import gl_model
        from . import gl_mesh
        from . import gl_context

        refdef = refdef_in

        # Get actual display size (glw_imp tracks real size after fullscreen toggle)
        width = glw_imp.width if glw_imp.width > 0 else (refdef.width if hasattr(refdef, 'width') else 800)
        height = glw_imp.height if glw_imp.height > 0 else (refdef.height if hasattr(refdef, 'height') else 600)
        fov_y = refdef.fov_y if hasattr(refdef, 'fov_y') else 75.0

        vieworg = refdef.vieworg if hasattr(refdef, 'vieworg') else [0, 0, 0]
        viewangles = refdef.viewangles if hasattr(refdef, 'viewangles') else [0, 0, 0]

        # Begin frame
        glw_imp.GLimp_BeginFrame(0)

        # Clear screen
        R_ClearScreen()

        # Set viewport
        if gl_context.ctx:
            gl_context.ctx.viewport = (0, 0, int(width), int(height))

            # Build projection and view matrices
            aspect = width / max(height, 1)
            proj = _make_projection_matrix(fov_y, aspect, 1.0, 4096.0)
            view = _make_view_matrix(vieworg, viewangles[0], viewangles[1], viewangles[2])

            # Upload matrices to shader uniforms (transpose for column-major)
            prog = gl_context.bsp_program
            if prog:
                prog['u_proj'].write(proj.T.tobytes())
                prog['u_view'].write(view.T.tobytes())
                prog['u_texture'].value = 0
                prog['u_lightmap'].value = 1
                prog['u_fullbright'].value = 1.0  # 1.0 = full bright, 0.0 = use lightmap

        # Render world
        rdflags = refdef.rdflags if hasattr(refdef, 'rdflags') else 0
        if not (rdflags & 1):  # RDF_NOWORLDMODEL = 1
            try:
                worldmodel = refdef.worldmodel if hasattr(refdef, 'worldmodel') else None
                if worldmodel and hasattr(gl_rsurf, 'R_DrawWorld'):
                    gl_rsurf.R_DrawWorld(worldmodel)
            except Exception as e:
                print(f"[GL_RMAIN] World render error: {e}")

        # Render entities
        try:
            R_DrawEntitiesOnList()
        except Exception as e:
            pass

        # Render dynamic lights
        try:
            from . import gl_light
            gl_light.R_RenderDlights()
        except Exception as e:
            pass

        # Render particles
        try:
            R_DrawParticles()
        except Exception as e:
            pass

        # Post-process effects
        try:
            R_PolyBlend()
        except Exception as e:
            pass

        # Draw 2D HUD
        # Disabled: gl_draw.py uses fixed-function OpenGL incompatible with Core Profile
        # TODO: Port 2D drawing to ModernGL shaders
        # try:
        #     from . import gl_draw
        #     gl_draw.DrawCrosshair()
        #     player_state = getattr(refdef, 'player_state', None)
        #     if player_state:
        #         gl_draw.SCR_DrawHUD(player_state)
        # except Exception as e:
        #     pass

        # End frame
        glw_imp.GLimp_EndFrame()

        return True

    except Exception as e:
        print(f"R_RenderFrame error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ===== Entity Rendering =====

def R_DrawEntitiesOnList():
    """Draw all entities in list"""
    try:
        from . import gl_model
        from . import gl_mesh

        if not refdef or not hasattr(refdef, 'entities'):
            return

        for ent in refdef.entities:
            if not ent:
                continue

            # Skip if no model
            if not ent.model:
                continue

            # Get model type
            model_type = ent.model.type if hasattr(ent.model, 'type') else None

            # Draw based on model type
            try:
                if model_type == 2:  # MODEL_ALIAS = 2 (MD2)
                    gl_mesh.R_DrawAliasModel(ent)
                elif model_type == 3:  # MODEL_SPRITE = 3
                    R_DrawSpriteModel(ent)
                elif model_type == 1:  # MODEL_BRUSH = 1
                    gl_model.R_DrawBrushModel(ent)
                else:
                    # Fallback - draw a placeholder
                    glPushMatrix()
                    glTranslatef(ent.origin[0], ent.origin[1], ent.origin[2])
                    R_DrawNullModel()
                    glPopMatrix()

            except Exception as e:
                # Draw null model as fallback
                glPushMatrix()
                glTranslatef(ent.origin[0], ent.origin[1], ent.origin[2])
                R_DrawNullModel()
                glPopMatrix()

    except Exception as e:
        print(f"R_DrawEntitiesOnList error: {e}")


def R_DrawSpriteModel(e):
    """Draw sprite model"""
    # TODO: Implement sprite rendering
    pass


def R_DrawNullModel():
    """Draw null model (placeholder cross)"""
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    # Draw X cross
    glVertex3f(-8, 0, 0)
    glVertex3f(8, 0, 0)
    glVertex3f(0, -8, 0)
    glVertex3f(0, 8, 0)
    glVertex3f(0, 0, -8)
    glVertex3f(0, 0, 8)
    glEnd()


def R_RotateForEntity(e):
    """Setup rotation matrix for entity"""
    # TODO: Apply entity angles
    pass


def R_CullBox(mins, maxs):
    """Frustum cull bounding box"""
    # TODO: Implement frustum culling
    return False  # Not culled


# ===== Particle Rendering =====

def R_DrawParticles():
    """Draw particle system"""
    # TODO: Implement particle rendering
    pass


def GL_DrawParticles(num_particles, particles, colortable):
    """Draw particles at GL level"""
    # TODO: Implement particle drawing
    pass


# ===== Post-Processing =====

def R_PolyBlend():
    """Apply color blending for damage/water/etc"""
    # TODO: Implement poly blend
    pass


# ===== Utilities =====

@TODO
def R_SpriteModel(e):
    pass


@TODO
def R_Trace(start, end, size):
    pass


@TODO
def R_InitParticleTexture():
    pass


@TODO
def Draw_InitLocal():
    pass


@TODO
def R_SubdivideSurface(fa):
    pass


@TODO
def R_BuildLightMaps():
    pass


# ===== Import after function definitions =====

try:
    from quake2.common import Com_Printf
except:
    def Com_Printf(msg):
        print(msg)
