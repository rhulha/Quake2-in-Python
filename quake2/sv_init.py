from .sv_main import server
from .cmodel import CM_LoadMap, CM_EntityString, CM_NumInlineModels, CM_InlineModel
from .sv_world import SV_ClearWorld


CS_MODELS = 1
CS_SOUNDS = 1024
CS_IMAGES = 2048

MAX_MODELS = 256
MAX_SOUNDS = 256
MAX_IMAGES = 256


def _ensure_server_tables():
    if not hasattr(server, "configstrings"):
        server.configstrings = {}
    if not hasattr(server, "baselines"):
        server.baselines = {}
    if not hasattr(server, "spawncount"):
        server.spawncount = 0
    if not hasattr(server, "state"):
        server.state = 0


def SV_FindIndex(name, start, max, create):
    _ensure_server_tables()
    if not name:
        return 0

    for i in range(1, max):
        key = start + i
        if key not in server.configstrings:
            break
        if server.configstrings[key] == name:
            return i
    else:
        i = max

    if not create:
        return 0
    if i >= max:
        raise RuntimeError("SV_FindIndex overflow")

    server.configstrings[start + i] = name
    return i


def SV_ModelIndex(name):
    return SV_FindIndex(name, CS_MODELS, MAX_MODELS, True)


def SV_SoundIndex(name):
    return SV_FindIndex(name, CS_SOUNDS, MAX_SOUNDS, True)


def SV_ImageIndex(name=None):
    return SV_FindIndex(name, CS_IMAGES, MAX_IMAGES, True)


def SV_CreateBaseline():
    _ensure_server_tables()
    server.baselines.clear()
    if not getattr(server, "edicts", None):
        return

    for entnum in range(1, len(server.edicts)):
        svent = server.edicts[entnum]
        if not svent or not getattr(svent, "inuse", False):
            continue

        s = getattr(svent, "s", None)
        if not s:
            continue
        if not getattr(s, "modelindex", 0) and not getattr(s, "sound", 0) and not getattr(s, "effects", 0):
            continue

        s.number = entnum
        if hasattr(s, "origin") and hasattr(s, "old_origin"):
            s.old_origin[:] = list(s.origin)
        server.baselines[entnum] = s


def SV_CheckForSavegame():
    # Savegame restore is not fully wired yet in the Python port.
    # Keep world links coherent for map transitions.
    SV_ClearWorld()


def SV_SpawnServer(mapname, spawnpoint, serverstate, attractloop, loadgame):
    _ensure_server_tables()

    server.spawncount += 1
    server.state = 0
    server.loadgame = bool(loadgame)
    server.attractloop = bool(attractloop)
    server.time = 0.0
    server.mapname = mapname
    server.name = mapname

    server.configstrings.clear()
    server.configstrings[0] = mapname

    if not getattr(server, "models", None):
        server.models = []
    if len(server.models) < 2:
        server.models = [None, None]

    checksum = None
    if serverstate != 2:
        server.models[1] = CM_LoadMap("", False, checksum)
    else:
        bsp_name = f"maps/{mapname}.bsp"
        server.configstrings[CS_MODELS + 1] = bsp_name
        server.models[1] = CM_LoadMap(bsp_name, False, checksum)

    SV_ClearWorld()

    num_inline = CM_NumInlineModels()
    needed = 2 + num_inline + 2
    if len(server.models) < needed:
        server.models.extend([None] * (needed - len(server.models)))

    for i in range(1, num_inline):
        key = CS_MODELS + 1 + i
        server.configstrings[key] = f"*{i}"
        server.models[i + 1] = CM_InlineModel(server.configstrings[key])

    server.state = 1
    try:
        from game.g_spawn import SpawnEntities
        SpawnEntities(mapname, CM_EntityString(), spawnpoint)
    except Exception:
        pass

    try:
        from game.g_main import G_RunFrame
        G_RunFrame()
        G_RunFrame()
    except Exception:
        pass

    server.state = serverstate
    SV_CreateBaseline()
    SV_CheckForSavegame()


def SV_InitGame():
    _ensure_server_tables()
    if not hasattr(server, "initialized"):
        server.initialized = False

    if not getattr(server, "edicts", None):
        server.edicts = [None] * server.max_edicts
    server.num_edicts = 0
    server.initialized = True
    server.spawncount += 1


def SV_Map(attractloop, levelstring, loadgame):
    if not getattr(server, "initialized", False) and not loadgame:
        SV_InitGame()

    level = str(levelstring)
    spawnpoint = ""

    if "+" in level:
        level = level.split("+", 1)[0]

    if "$" in level:
        level, spawnpoint = level.split("$", 1)

    if level.endswith(".cin") or level.endswith(".pcx") or level.endswith(".dm2"):
        server.state = 2
        server.mapname = level
        return

    if level.startswith("*"):
        level = level[1:]

    SV_SpawnServer(level, spawnpoint, 2, attractloop, loadgame)
