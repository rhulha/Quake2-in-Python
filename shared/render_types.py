"""
Quake 2 rendering data structures.
Corresponds to C structures in client/ref.h and client/client.h
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class lightstyle_t:
    """Light style for animated lights (e.g., pulsing effects)"""
    rgb: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    white: float = 1.0


@dataclass
class entity_t:
    """Entity state for rendering"""
    model: Optional[Any] = None
    angles: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    frame: int = 0
    oldorigin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    oldframe: int = 0
    backlerp: float = 0.0
    skinnum: int = 0
    lightstyle: int = 0
    alpha: float = 1.0
    skin: Optional[Any] = None
    flags: int = 0


@dataclass
class dlight_t:
    """Dynamic light for real-time lighting"""
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    color: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    intensity: float = 1.0


@dataclass
class particle_t:
    """Particle for effects and explosions"""
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    color: List[int] = field(default_factory=lambda: [255, 255, 255])
    alpha: float = 1.0


@dataclass
class refdef_t:
    """Rendering frame definition - passed to renderer each frame"""
    # Viewport
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600

    # View parameters
    fov_x: float = 90.0
    fov_y: float = 75.0
    vieworg: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    viewangles: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])

    # Post-processing
    blend: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])  # RGBA
    time: float = 0.0

    # Rendering flags
    rdflags: int = 0
    areabits: bytes = b''

    # Lights and styles
    lightstyles: List[lightstyle_t] = field(default_factory=list)

    # Scene contents
    entities: List[entity_t] = field(default_factory=list)
    dlights: List[dlight_t] = field(default_factory=list)
    particles: List[particle_t] = field(default_factory=list)

    # World model reference
    worldmodel: Optional[Any] = None
