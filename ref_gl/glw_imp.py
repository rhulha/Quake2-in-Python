"""
glw_imp.py - OpenGL window implementation using pygame
Handles window creation, context, and frame management
"""

import pygame
from OpenGL.GL import *
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error"])

# ===== Global State =====

window = None
context = None
width = 0
height = 0
fullscreen = False
initialized = False

# ===== Window Management =====

def VID_CreateWindow(window_width, window_height, is_fullscreen=False):
    """Create OpenGL window via pygame"""
    global window, width, height, fullscreen, initialized

    width = window_width
    height = window_height
    fullscreen = is_fullscreen

    try:
        # Initialize pygame if needed
        if not pygame.get_init():
            pygame.init()

        # Set OpenGL attributes before window creation
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_RED_SIZE, 8)
        pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE, 8)
        pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE, 8)

        # Create window
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if is_fullscreen:
            flags |= pygame.FULLSCREEN

        window = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Quake 2")

        initialized = True

        Com_Printf(f"Created OpenGL window: {width}x{height} fullscreen={is_fullscreen}\n")
        return True

    except Exception as e:
        Com_Printf(f"Error creating window: {e}\n")
        return False


def GLimp_SetMode(pwidth, pheight, mode, fullscreen):
    """Set video mode (Quake 2 compatibility function)"""
    if VID_CreateWindow(pwidth.GetValue() if hasattr(pwidth, 'GetValue') else pwidth,
                       pheight.GetValue() if hasattr(pheight, 'GetValue') else pheight,
                       fullscreen):
        if hasattr(pwidth, 'SetValue'):
            pwidth.SetValue(width)
        if hasattr(pheight, 'SetValue'):
            pheight.SetValue(height)
        return True
    return False


def GLimp_Init(hinstance=None, wndproc=None):
    """Initialize OpenGL implementation"""
    global initialized

    if not initialized:
        if not VID_CreateWindow(800, 600, False):
            Com_Error(0, "GLimp_Init: couldn't create window")
            return False

    GLimp_InitGL()
    return True


def GLimp_InitGL():
    """Initialize OpenGL state via ModernGL"""
    try:
        from . import gl_context
        gl_context.init()
        Com_Printf("ModernGL 3.3 Core context initialized\n")
        return True

    except Exception as e:
        Com_Printf(f"GLimp_InitGL error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def GLimp_Shutdown():
    """Shutdown OpenGL"""
    global window, initialized

    if window:
        pygame.display.quit()
        window = None

    initialized = False
    Com_Printf("OpenGL shutdown\n")


def GLimp_BeginFrame(camera_separation=0):
    """Prepare for frame rendering"""
    # Modern GL 3.3 Core uses matrix uniforms instead of matrix stack
    # Matrix setup is now done in gl_rmain.py
    pass


def GLimp_EndFrame():
    """Finish frame rendering and swap buffers"""
    try:
        pygame.display.flip()
    except:
        pass


def GLimp_AppActivate(active):
    """Handle window activation/deactivation"""
    pass


def VerifyDriver():
    """Verify OpenGL driver is working"""
    try:
        vendor = glGetString(GL_VENDOR)
        renderer = glGetString(GL_RENDERER)
        version = glGetString(GL_VERSION)

        if vendor:
            vendor = vendor.decode('utf-8') if isinstance(vendor, bytes) else str(vendor)
        if renderer:
            renderer = renderer.decode('utf-8') if isinstance(renderer, bytes) else str(renderer)
        if version:
            version = version.decode('utf-8') if isinstance(version, bytes) else str(version)

        Com_Printf(f"GL_VENDOR: {vendor}\n")
        Com_Printf(f"GL_RENDERER: {renderer}\n")
        Com_Printf(f"GL_VERSION: {version}\n")

        return True

    except Exception as e:
        Com_Printf(f"VerifyDriver error: {e}\n")
        return False


# ===== Utility Functions =====

def GLimp_GetProcAddress(name):
    """Get OpenGL function pointer (for extensions)"""
    # In Python with PyOpenGL, this is handled automatically
    # Just return a placeholder
    return None


from quake2.common import Com_Printf, Com_Error
