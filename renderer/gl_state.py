from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

@dataclass
class GLConfig:
    """Immutable GL capabilities and vendor info."""
    renderer: str = ""
    vendor: str = ""
    version: str = ""
    extensions: str = ""
    allow_cds: bool = True

@dataclass
class GLState:
    """Mutable GL state (textures, matrices, blend modes, etc.)."""
    inverse_intensity: float = 1.0
    fullscreen: bool = False
    prev_mode: int = 0

    # Texture binding state
    current_textures: List[int] = field(default_factory=lambda: [0, 0])
    current_tmu: int = 0  # texture multiple unit

    # Stereo rendering
    camera_separation: float = 0.0
    stereo_enabled: bool = False

    # Gamma correction
    original_gamma_table: np.ndarray = field(default_factory=lambda: np.ones(256, dtype=np.uint8))

    # Lightmap state
    lightmap_textures: List[int] = field(default_factory=list)
    lightmap_buffer: Optional[np.ndarray] = None
    allocated: List[int] = field(default_factory=lambda: [0] * 128)

    def reset(self):
        """Reset state to defaults."""
        self.inverse_intensity = 1.0
        self.current_textures = [0, 0]
        self.current_tmu = 0
        self.camera_separation = 0.0
        self.stereo_enabled = False

@dataclass
class CVarStub:
    """Simplified cvar (console variable) placeholder."""
    name: str
    value: str = "0"
    integer: int = 0
    floating: float = 0.0

    def set(self, value):
        """Set value as string and parse to typed versions."""
        self.value = str(value)
        try:
            self.integer = int(value)
            self.floating = float(value)
        except ValueError:
            self.integer = 0
            self.floating = 0.0

class CVarManager:
    """Simple cvar registry. Stubs out the engine's cvar system."""

    def __init__(self):
        self.cvars: Dict[str, CVarStub] = {}
        self._init_defaults()

    def _init_defaults(self):
        """Initialize default cvars used by renderer."""
        defaults = {
            # Rendering
            'r_norefresh': '0',
            'r_lefthand': '0',
            'r_drawentities': '1',
            'r_drawworld': '1',
            'r_speeds': '0',
            'r_fullbright': '0',
            'r_novis': '0',
            'r_nocull': '0',
            'r_lerpmodels': '1',
            'r_lightlevel': '0',

            # GL-specific
            'gl_vertex_arrays': '1',
            'gl_ext_swapinterval': '1',
            'gl_ext_palettedtexture': '0',
            'gl_ext_multitexture': '1',
            'gl_ext_pointparameters': '0',
            'gl_ext_compiled_vertex_array': '0',

            # Particles
            'gl_particle_min_size': '2',
            'gl_particle_max_size': '40',
            'gl_particle_size': '40',
            'gl_particle_att_a': '0.01',
            'gl_particle_att_b': '0.0',
            'gl_particle_att_c': '0.01',

            # Textures
            'gl_nosubimage': '0',
            'gl_bitdepth': '0',
            'gl_mode': '3',
            'gl_log': '0',
            'gl_lightmap': '0',
            'gl_shadows': '0',
            'gl_dynamic': '1',
            'gl_monolightmap': '0',
            'gl_nobind': '0',
            'gl_round_down': '1',
            'gl_picmip': '0',
            'gl_skymip': '0',
            'gl_showtris': '0',
            'gl_finish': '0',
            'gl_ztrick': '1',
            'gl_clear': '0',
            'gl_cull': '1',
            'gl_poly': '0',
            'gl_texsort': '1',
            'gl_polyblend': '1',
            'gl_flashblend': '0',
            'gl_lightmaptype': '0',
            'gl_modulate': '1.0',
            'gl_playermip': '0',
            'gl_drawbuffer': '1',
            'gl_3dlabs_broken': '0',
            'gl_driver': 'opengl32',
            'gl_swapinterval': '0',
            'gl_texturemode': 'GL_LINEAR_MIPMAP_NEAREST',
            'gl_texturealphamode': 'default',
            'gl_texturesolidmode': 'default',
            'gl_saturatelighting': '0',
            'gl_lockpvs': '0',

            # Video
            'vid_fullscreen': '0',
            'vid_gamma': '1.0',

            # Lighting
            'intensity': '2.0',
        }
        for name, value in defaults.items():
            cvar = CVarStub(name, value)
            cvar.set(value)
            self.cvars[name] = cvar

    def get(self, name: str, default: str = "0") -> CVarStub:
        """Get or create cvar."""
        if name not in self.cvars:
            cvar = CVarStub(name, default)
            cvar.set(default)
            self.cvars[name] = cvar
        return self.cvars[name]

    def set(self, name: str, value):
        """Set cvar value."""
        cvar = self.get(name)
        cvar.set(value)

    def set_value(self, name: str, value: float):
        """Set cvar as float."""
        self.set(name, str(value))

# Global instances
gl_config = GLConfig()
gl_state = GLState()
cvar_manager = CVarManager()
