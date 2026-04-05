"""
gl_screenshot.py - Screenshot capture functionality
Captures the current OpenGL framebuffer and saves to PNG
"""

import os
from datetime import datetime
from OpenGL.GL import *
import pygame


def take_screenshot(width, height, output_dir="screenshots"):
    """
    Capture the current OpenGL framebuffer and save as PNG

    Args:
        width: Framebuffer width
        height: Framebuffer height
        output_dir: Directory to save screenshots

    Returns:
        Path to saved screenshot, or None if failed
    """
    try:
        # Create output directory if needed
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Flush OpenGL commands before reading
        glFlush()
        glFinish()

        # Read from front buffer explicitly (for double-buffered setup)
        glReadBuffer(GL_FRONT)

        # Read pixels from OpenGL framebuffer
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)

        # Convert to pygame surface
        # pixels is a flat bytes object, need to reshape it
        pixel_array = bytearray(pixels)

        # Create pygame surface from pixel data
        surface = pygame.image.fromstring(bytes(pixel_array), (width, height), "RGB")

        # Flip vertically because OpenGL reads bottom-up
        surface = pygame.transform.flip(surface, False, True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quake2_screenshot_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        # Save the screenshot
        pygame.image.save(surface, filepath)

        print(f"Screenshot saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"Screenshot error: {e}")
        return None
