import math


class _ViewState:
    entities = []
    particles = []
    dlights = []
    lightstyles = [[1.0, 1.0, 1.0] for _ in range(64)]
    gun_model_index = 0
    gun_frame = 0
    prepared = False
    crosshair = "+"
    last_refdef = {}


def V_ClearScene():
    _ViewState.entities = []
    _ViewState.particles = []
    _ViewState.dlights = []


def V_AddEntity(ent):
    if ent is None:
        return
    _ViewState.entities.append(ent)


def V_AddParticle(org, color, alpha):
    _ViewState.particles.append({
        "org": list(org),
        "color": int(color),
        "alpha": float(alpha),
    })


def V_AddLight(org, intensity, r, g, b):
    _ViewState.dlights.append({
        "org": list(org),
        "intensity": float(intensity),
        "color": [float(r), float(g), float(b)],
    })


def V_AddLightStyle(style, r, g, b):
    if 0 <= style < len(_ViewState.lightstyles):
        _ViewState.lightstyles[style] = [float(r), float(g), float(b)]


def V_TestParticles():
    for i in range(32):
        V_AddParticle([float(i * 2), 0.0, 24.0], i & 255, 1.0)


def V_TestEntities():
    for i in range(8):
        V_AddEntity({
            "origin": [float(i * 32), 0.0, 16.0],
            "angles": [0.0, 0.0, 0.0],
            "modelindex": 1,
        })


def V_TestLights():
    for i in range(8):
        V_AddLight([float(i * 64), 0.0, 64.0], 200.0, 1.0, 0.75, 0.5)


def CL_PrepRefresh():
    _ViewState.prepared = True
    V_ClearScene()


def CalcFov(fov_x, width, height):
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


def V_RenderView(stereo_separation):
    if not _ViewState.prepared:
        CL_PrepRefresh()

    refdef = {
        "stereo": float(stereo_separation),
        "entities": list(_ViewState.entities),
        "particles": list(_ViewState.particles),
        "dlights": list(_ViewState.dlights),
        "lightstyles": list(_ViewState.lightstyles),
        "gun_model_index": _ViewState.gun_model_index,
        "gun_frame": _ViewState.gun_frame,
    }
    _ViewState.last_refdef = refdef

    try:
        from . import vid_dll
        if hasattr(vid_dll, "R_RenderFrame"):
            vid_dll.R_RenderFrame(refdef)
    except Exception:
        return refdef

    return refdef


def V_Viewpos_f():
    ref = _ViewState.last_refdef
    if not ref:
        return "view not rendered"
    return f"ents={len(ref['entities'])} particles={len(ref['particles'])} lights={len(ref['dlights'])}"


def V_Init():
    _ViewState.gun_model_index = 0
    _ViewState.gun_frame = 0
    _ViewState.prepared = False
    _ViewState.last_refdef = {}
    V_ClearScene()
