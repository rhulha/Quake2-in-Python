"""
gl_context.py - ModernGL context and shader program management
Created once at window initialization, imported by gl_rsurf and gl_rmain.
"""

import moderngl

ctx = None
bsp_program = None


def init():
    """Initialize ModernGL context and compile BSP shader program"""
    global ctx, bsp_program

    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    ctx.cull_face = 'back'
    ctx.front_face = 'cw'
    ctx.depth_func = '<='

    from . import shaders
    bsp_program = ctx.program(
        vertex_shader=shaders.BSP_VERT,
        fragment_shader=shaders.BSP_FRAG,
    )


def shutdown():
    """Release ModernGL resources"""
    global ctx, bsp_program
    if bsp_program:
        bsp_program.release()
        bsp_program = None
    if ctx:
        ctx.release()
        ctx = None
