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


def V_RenderView(fov_x=90.0, width=800, height=600):
    """Build refdef and render frame"""
    global client

    if not _ViewState.prepared:
        CL_PrepRefresh()

    # Get player viewpoint from server state (for single-player)
    try:
        from . import sv_main
        if sv_main.server.edicts and len(sv_main.server.edicts) > 0:
            player = sv_main.server.edicts[0]  # Entity 0 is the player
            if player and hasattr(player, 'origin') and hasattr(player, 'angles'):
                _ViewState.vieworg = list(player.origin) if hasattr(player.origin, '__iter__') else [0, 0, 0]
                _ViewState.viewangles = list(player.angles) if hasattr(player.angles, '__iter__') else [0, 0, 0]
    except:
        pass

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
