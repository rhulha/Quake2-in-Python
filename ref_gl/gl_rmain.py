"""
gl_rmain.py - OpenGL main renderer
Handles initialization, frame rendering, and view setup
"""

import math
from OpenGL.GL import *
from OpenGL.GL import glFrustum as GLFrustum
from wrapper_qpy.decorators import va_args, TODO
from wrapper_qpy.custom_classes import Mutable

# ===== Global State =====

refdef = None
glstate = {
    'currenttextures': [0, 0],
    'currentmatrix': None,
}

# ===== Initialization =====

def R_Init():
    """Initialize OpenGL renderer"""
    try:
        from . import glw_imp
        try:
            from quake2.common import Com_Printf, Cvar_Get
        except ImportError:
            from ..quake2.common import Com_Printf, Cvar_Get

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

        Com_Printf("R_Init complete\n")
        return True

    except Exception as e:
        print(f"R_Init error: {e}")
        return False


def R_Shutdown():
    """Shutdown renderer"""
    try:
        from . import glw_imp
        from ..quake2.common import Com_Printf

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
    near = 4.0
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
    """Clear framebuffer"""
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


# ===== Rendering =====

def R_RenderFrame(refdef_in):
    """Main frame rendering function"""
    global refdef

    try:
        from . import glw_imp
        from . import gl_rsurf
        from . import gl_model
        from . import gl_mesh

        refdef = refdef_in

        # Get refdef dimensions
        width = refdef.width if hasattr(refdef, 'width') else 800
        height = refdef.height if hasattr(refdef, 'height') else 600
        fov_y = refdef.fov_y if hasattr(refdef, 'fov_y') else 75.0

        # Begin frame
        glw_imp.GLimp_BeginFrame(0)

        # Clear screen
        R_ClearScreen()

        # Setup viewport and projection
        R_SetupViewport(width, height, fov_y)

        # Setup camera matrices
        R_SetupMatrices(refdef)

        # Render world
        rdflags = refdef.rdflags if hasattr(refdef, 'rdflags') else 0
        if not (rdflags & 1):  # RDF_NOWORLDMODEL = 1
            try:
                # Get world model
                worldmodel = refdef.worldmodel if hasattr(refdef, 'worldmodel') else None
                if worldmodel and hasattr(gl_rsurf, 'R_DrawWorld'):
                    gl_rsurf.R_DrawWorld(worldmodel)
            except Exception as e:
                pass

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
        try:
            from . import gl_draw
            gl_draw.DrawCrosshair()

            # Draw HUD stats (if available)
            player_state = getattr(refdef, 'player_state', None)
            if player_state:
                gl_draw.SCR_DrawHUD(player_state)

        except Exception as e:
            pass

        # End frame
        glw_imp.GLimp_EndFrame()

        return True

    except Exception as e:
        print(f"R_RenderFrame error: {e}")
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
    from ..quake2.common import Com_Printf
except:
    def Com_Printf(msg):
        print(msg)
