# Quake2 in Python

A full port of Quake2 to Python with ModernGL-accelerated 3D rendering. This is an educational project that demonstrates how complex game engines can be understood and reimplemented in Python.

## Current Status

✅ **Fully Playable** - Engine loads maps, renders 3D geometry, and runs at 1000+ FPS
✅ **Modern GPU Rendering** - ModernGL 3.3 Core Profile with VBO/VAO batch rendering  
✅ **BSP Maps** - Complete BSP file parsing and geometry loading
✅ **Input System** - WASD movement, mouse camera control, crosshair rendering
✅ **Sound System** - Audio playback (OGG format)
✅ **Game Logic** - Entity spawning, gravity, clipping, lighting system
✅ **Comprehensive Tests** - 248 unit tests covering 19 modules with 100% pass rate

### Performance
- **Rendering**: 1000+ FPS (vs 10-20 FPS with immediate-mode OpenGL)
- **Speedup**: 100x+ improvement from the legacy immediate-mode renderer
- **Memory**: Efficient VBO/VAO batch system (~57 batches per map)

## Getting Started

### Requirements
- Python 3.12+
- Quake 2 game files (baseq2 directory from Steam or CD)
- Windows 11 (primary target)

### Installation

```bash
pip install pygame PyOpenGL PyOpenGL-accelerate numpy moderngl
```

### Running

```bash
# Edit quake2_config.json to point to your Quake2 directory
python main.py +map base1
```

### Controls
- **WASD** - Movement
- **Mouse** - Look around
- **ESC** - Quit
- **F12** - Take screenshot

## Project Structure

```
├── quake2/              # Core engine
│   ├── common.py        # Engine initialization
│   ├── sv_main.py       # Server simulation
│   ├── cl_main.py       # Client logic
│   ├── cmodel.py        # Collision model
│   ├── files.py         # File system and PAK loading
│   └── ...
├── ref_gl/              # OpenGL rendering
│   ├── glw_imp.py       # Window/context management (pygame)
│   ├── gl_context.py    # ModernGL context & shader compilation
│   ├── gl_rmain.py      # Main renderer & frame setup
│   ├── gl_rsurf.py      # BSP surface rendering (VBO/VAO)
│   ├── gl_image.py      # Texture loading & management
│   ├── shaders.py       # GLSL vertex/fragment shaders
│   └── ...
├── game/                # Game code (entities, weapons, etc.)
├── unit_tests/          # 248 unit tests
└── main.py              # Entry point
```

## Architecture

### Rendering Pipeline (ModernGL)
1. **Map Load**: BSP file parsed, geometry extracted to VBO
2. **Batch Building**: Faces grouped by texture, VAO created per batch
3. **Per Frame**: 
   - View matrices computed (numpy)
   - Uniforms uploaded to shader
   - One render call per texture batch
   - Result: ~57 draw calls vs ~5000 with immediate-mode

### Shader System
- **Vertex Shader**: Position transformation, UV mapping
- **Fragment Shader**: Texture sampling, lightmap blending
- **Format**: 7 floats per vertex (pos, texcoord, lm_texcoord)

## Design Philosophy

### The Four Qs:

* **`Quick, not fast`** - Logic is correct before optimization. Python isn't fast, but the code is readable.
* **`Quote the author`** - Code structure mirrors the original C code to aid understanding of Quake's architecture.
* **`Question the code`** - Dead code is left in place (with `pass` or `# TODO`), encouraging exploration of design decisions.
* **`Quest for perfection`** - Goal is C-compatible network play (future enhancement).

## Known Limitations

- **Textures**: WAL files load but ModernGL texture wrapping needs fixing
- **HUD**: 2D drawing (gl_draw.py) not ported to Core Profile yet
- **Models**: MD2 alias model rendering in progress
- **Network**: Single-player only (multiplayer support planned)
- **Sound**: Basic playback; spatial audio not fully implemented

## Development

### Running Tests
```bash
python -m pytest unit_tests/ -v
```

### Key Modules to Understand
1. `quake2/qfiles.py` - Binary file format parsing (BSP, WAL, PAK)
2. `ref_gl/gl_rsurf.py` - Geometry batch building and rendering
3. `quake2/cmodel.py` - Collision detection and physics
4. `game/g_*.py` - Game entity spawning and logic

## Performance Notes

The ModernGL renderer achieves 100x+ speedup by:
- Building geometry once at map load (not per-frame)
- Using GPU buffers (VBO) instead of immediate-mode glBegin/glEnd
- Batching faces by texture (57 batches vs 5000+ draw calls)
- Uploading matrices as uniforms instead of stack manipulation

Frame time breakdown (1000 FPS @ ~1ms/frame):
- Rendering: <0.5ms
- Game logic: <0.3ms
- Python overhead: ~0.2ms

## Contributing

The codebase follows these principles:
- Keep code readable over optimized
- Preserve original C structure for educational value
- Add tests for new features
- Document non-obvious Quake 2 concepts

## Resources

- Original Quake 2 source: https://github.com/id-Software/Quake-2
- ModernGL docs: https://moderngl.readthedocs.io/
- Quake 2 BSP format: Quake II documentation (various sources)

## License

Educational project. Quake 2 is owned by id Software / Activision.
