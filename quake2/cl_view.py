import math
import time
from shared.render_types import refdef_t, entity_t, dlight_t, particle_t, lightstyle_t


class _ViewState:
    entities = []
    particles = []
    dlights = []
    lightstyles = [lightstyle_t() for _ in range(64)]
    gun_model_index = 0
    gun_frame = 0
    prepared = False
    crosshair = "+"
    last_refdef = None
    vieworg = [0.0, 0.0, 0.0]
    viewangles = [0.0, 0.0, 0.0]
    worldmodel = None
    current_mapname = None
    spawned = False  # Track if we've set initial spawn position


def V_ClearScene():
    _ViewState.entities = []
    _ViewState.particles = []
    _ViewState.dlights = []


def V_AddEntity(ent):
    """Add entity to render list"""
    if ent is None:
        return

    # Convert dict-style entities to entity_t if needed
    if isinstance(ent, dict):
        ent = entity_t(
            model=ent.get('model'),
            angles=ent.get('angles', [0.0, 0.0, 0.0]),
            origin=ent.get('origin', [0.0, 0.0, 0.0]),
            frame=ent.get('frame', 0),
            oldorigin=ent.get('oldorigin', [0.0, 0.0, 0.0]),
            oldframe=ent.get('oldframe', 0),
            backlerp=ent.get('backlerp', 0.0),
            skinnum=ent.get('skinnum', 0),
            lightstyle=ent.get('lightstyle', 0),
            alpha=ent.get('alpha', 1.0),
            skin=ent.get('skin'),
            flags=ent.get('flags', 0),
        )

    _ViewState.entities.append(ent)


def V_AddParticle(org, color, alpha):
    """Add particle to render list"""
    p = particle_t(
        origin=list(org) if hasattr(org, '__iter__') else [org, 0.0, 0.0],
        color=[int(color) >> 16 & 0xFF, int(color) >> 8 & 0xFF, int(color) & 0xFF],
        alpha=float(alpha),
    )
    _ViewState.particles.append(p)


def V_AddLight(org, intensity, r, g, b):
    """Add dynamic light to render list"""
    d = dlight_t(
        origin=list(org) if hasattr(org, '__iter__') else [org, 0.0, 0.0],
        color=[float(r), float(g), float(b)],
        intensity=float(intensity),
    )
    _ViewState.dlights.append(d)


def V_AddLightStyle(style, r, g, b):
    """Update light style animation"""
    if 0 <= style < len(_ViewState.lightstyles):
        _ViewState.lightstyles[style] = lightstyle_t(
            rgb=[float(r), float(g), float(b)],
            white=max(r, g, b)
        )


def V_TestParticles():
    """Debug: add test particles"""
    for i in range(32):
        V_AddParticle([float(i * 2), 0.0, 24.0], i & 255, 1.0)


def V_TestEntities():
    """Debug: add test entities"""
    for i in range(8):
        V_AddEntity(entity_t(
            origin=[float(i * 32), 0.0, 16.0],
            angles=[0.0, 0.0, 0.0],
            modelindex=1,
        ))


def V_TestLights():
    """Debug: add test lights"""
    for i in range(8):
        V_AddLight([float(i * 64), 0.0, 64.0], 200.0, 1.0, 0.75, 0.5)


def CL_PrepRefresh():
    """Prepare for rendering"""
    _ViewState.prepared = True

    # Initialize renderer if not already done
    try:
        from ref_gl import gl_rmain
        gl_rmain.R_Init()
    except Exception as e:
        print(f"CL_PrepRefresh R_Init error: {e}")

    V_ClearScene()


def CalcFov(fov_x, width, height):
    """Calculate vertical FOV from horizontal FOV"""
    if fov_x < 1:
        fov_x = 1
    if fov_x > 179:
        fov_x = 179
    x = width / math.tan(fov_x / 360.0 * math.pi)
    a = math.atan(height / x)
    return a * 360.0 / math.pi


def V_Gun_Next_f():
    _ViewState.gun_frame += 1


def V_Gun_Prev_f():
    _ViewState.gun_frame -= 1
    if _ViewState.gun_frame < 0:
        _ViewState.gun_frame = 0


def V_Gun_Model_f(model_index=None):
    if model_index is None:
        _ViewState.gun_model_index += 1
    else:
        _ViewState.gun_model_index = int(model_index)
    return _ViewState.gun_model_index


def SCR_DrawCrosshair():
    return _ViewState.crosshair


def _find_spawn_point():
    """Parse BSP entity string to find info_player_start origin."""
    try:
        from quake2 import cmodel
        estr = cmodel.entity_string
        if not estr:
            return None
        # Parse entity blocks: { "key" "value" ... }
        i = 0
        while i < len(estr):
            i = estr.find('{', i)
            if i == -1:
                break
            end = estr.find('}', i)
            if end == -1:
                break
            block = estr[i+1:end]
            i = end + 1
            keys = {}
            j = 0
            while j < len(block):
                q1 = block.find('"', j)
                if q1 == -1:
                    break
                q2 = block.find('"', q1 + 1)
                q3 = block.find('"', q2 + 1)
                q4 = block.find('"', q3 + 1)
                if q4 == -1:
                    break
                keys[block[q1+1:q2]] = block[q3+1:q4]
                j = q4 + 1
            if keys.get('classname') == 'info_player_start':
                origin_str = keys.get('origin', '')
                if origin_str:
                    parts = origin_str.split()
                    if len(parts) == 3:
                        return [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        pass
    return None


def V_RenderView(fov_x=90.0, width=800, height=600):
    """Build refdef and render frame"""
    global client

    if not _ViewState.prepared:
        CL_PrepRefresh()

    # Set initial camera position from player spawn point (only once per map load)
    if not _ViewState.spawned:
        spawn_origin = _find_spawn_point()
        if spawn_origin:
            _ViewState.vieworg = spawn_origin
            _ViewState.spawned = True

    # Local camera angles and movement from input system.
    # Use client-side movement instead of waiting for server updates (single-player camera control)
    try:
        from . import cl_input
        _ViewState.viewangles = list(cl_input._State.viewangles)

        # Apply WASD movement to camera position
        try:
            cmd = cl_input.CL_CreateCmd()
            frametime = cl_input._State.frametime
            _ViewState.vieworg = cl_input.CL_ApplyMovement(cmd, _ViewState.vieworg, _ViewState.viewangles, frametime)

        except Exception as move_err:
            print(f"[MOVEMENT ERROR] {move_err}")
    except Exception as e:
        print(f"[INPUT ERROR] {e}")

    # Load world model if map changed
    worldmodel = _ViewState.worldmodel
    try:
        from . import sv_main
        from ref_gl import gl_model

        mapname = sv_main.server.mapname if hasattr(sv_main.server, 'mapname') else ""
        if mapname and mapname != _ViewState.current_mapname:
            bsp_path = f"maps/{mapname}.bsp"
            worldmodel = gl_model.Mod_ForName(bsp_path, False)
            _ViewState.worldmodel = worldmodel
            _ViewState.current_mapname = mapname
            _ViewState.spawned = False  # Reset so we pick up new spawn point
            try:
                from . import cl_input
                cl_input._State.velocity = [0.0, 0.0, 0.0]
                cl_input._State.on_ground = False
            except Exception:
                pass
    except Exception as e:
        pass

    # Build refdef_t
    fov_y = CalcFov(fov_x, width, height)

    refdef = refdef_t(
        x=0,
        y=0,
        width=width,
        height=height,
        fov_x=float(fov_x),
        fov_y=float(fov_y),
        vieworg=_ViewState.vieworg,
        viewangles=_ViewState.viewangles,
        blend=[0.0, 0.0, 0.0, 0.0],
        time=time.time(),
        rdflags=0,
        areabits=b'',
        lightstyles=list(_ViewState.lightstyles),
        entities=list(_ViewState.entities),
        dlights=list(_ViewState.dlights),
        particles=list(_ViewState.particles),
        worldmodel=worldmodel,
    )

    _ViewState.last_refdef = refdef

    # Render the frame
    try:
        from ref_gl import gl_rmain
        gl_rmain.R_RenderFrame(refdef)
    except Exception as e:
        print(f"V_RenderView error: {e}")

    return refdef


def V_Viewpos_f():
    """Debug: show view info"""
    ref = _ViewState.last_refdef
    if not ref:
        return "view not rendered"
    return f"ents={len(ref.entities)} particles={len(ref.particles)} lights={len(ref.dlights)} pos={ref.vieworg}"


def V_Init():
    """Initialize view system"""
    _ViewState.gun_model_index = 0
    _ViewState.gun_frame = 0
    _ViewState.prepared = False
    _ViewState.last_refdef = None
    _ViewState.vieworg = [0.0, 0.0, 0.0]
    _ViewState.viewangles = [0.0, 0.0, 0.0]
    V_ClearScene()
