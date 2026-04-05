import pygame
import moderngl
import numpy as np

class GLContext:
    """ModernGL context manager using pygame backend."""

    def __init__(self, width=1024, height=768, fullscreen=False, vsync=True):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.ctx = None
        self.surface = None
        self.clock = None

    def init(self):
        """Initialize pygame and ModernGL context."""
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        flags = pygame.DOUBLEBUF | pygame.OPENGL
        if self.fullscreen:
            flags |= pygame.FULLSCREEN

        self.surface = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("Quake 2 - Python/OpenGL")

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.front_face = 'cw'  # Quake uses front-face culling
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear_color = (0.0, 0.0, 0.0, 1.0)

        if self.vsync:
            self.ctx.enable(moderngl.VSYNC)

        self.clock = pygame.time.Clock()
        return self.ctx

    def clear(self):
        """Clear color and depth buffers."""
        self.ctx.clear()

    def swap_buffers(self):
        """Swap front and back buffers."""
        pygame.display.flip()

    def poll_events(self):
        """Poll input events. Return False if quit requested."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True

    def tick(self, fps=60):
        """Limit frame rate."""
        self.clock.tick(fps)
        dt = self.clock.get_time() / 1000.0
        return dt

    def shutdown(self):
        """Clean up."""
        if self.surface:
            pygame.quit()

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, *args):
        self.shutdown()


if __name__ == '__main__':
    with GLContext(1024, 768) as gl:
        running = True
        while running:
            gl.clear()
            gl.swap_buffers()
            dt = gl.tick(60)
            running = gl.poll_events()
        print("Closed successfully")
