from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

_explosions = []
_beams = []
_lasers = []
_sustains = []


def CL_RegisterTEntSounds():
    return


def CL_RegisterTEntModels():
    return


def CL_ClearTEnts():
    global _explosions, _beams, _lasers, _sustains
    _explosions = []
    _beams = []
    _lasers = []
    _sustains = []


def CL_AllocExplosion():
    ex = {'ent': {'origin': [0.0, 0.0, 0.0], 'angles': [0.0, 0.0, 0.0],
                  'flags': 0, 'model': None, 'frame': 0},
          'type': 0, 'start': 0, 'frames': 0, 'baseframe': 0,
          'light': 0.0, 'lightcolor': [0.0, 0.0, 0.0]}
    _explosions.append(ex)
    return ex


def CL_SmokeAndFlash(origin):
    return


def CL_ParseParticles():
    try:
        from .common import MSG_ReadPos, MSG_ReadDir, MSG_ReadByte, msg_read as nm
        pos = [0.0, 0.0, 0.0]
        d = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadDir(nm, d)
        MSG_ReadByte(nm)
        MSG_ReadByte(nm)
    except Exception:
        return


def CL_ParseBeam(model):
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, msg_read as nm
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadPos(nm, pos)
    except Exception:
        return
    return 0


def CL_ParseBeam2(model):
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, MSG_ReadByte, msg_read as nm
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadPos(nm, pos)
        MSG_ReadByte(nm)
    except Exception:
        return
    return 0


def CL_ParsePlayerBeam(model):
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, MSG_ReadDir, msg_read as nm
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        d = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadPos(nm, pos)
        MSG_ReadDir(nm, d)
    except Exception:
        return
    return 0


def CL_ParseLightning(model):
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, msg_read as nm
        MSG_ReadShort(nm)
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadPos(nm, pos)
    except Exception:
        return
    return 0


def CL_ParseLaser(colors):
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, msg_read as nm
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadPos(nm, pos)
    except Exception:
        return


def CL_ParseSteam():
    try:
        from .common import (MSG_ReadShort, MSG_ReadPos, MSG_ReadDir,
                              MSG_ReadByte, MSG_ReadLong, msg_read as nm)
        MSG_ReadShort(nm)
        MSG_ReadByte(nm)
        pos = [0.0, 0.0, 0.0]
        d = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadDir(nm, d)
        MSG_ReadByte(nm)
        MSG_ReadShort(nm)
        MSG_ReadShort(nm)
        MSG_ReadLong(nm)
    except Exception:
        return


def CL_ParseWidow():
    try:
        from .common import MSG_ReadShort, MSG_ReadPos, msg_read as nm
        MSG_ReadShort(nm)
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
    except Exception:
        return


def CL_ParseNuke():
    try:
        from .common import MSG_ReadPos, MSG_ReadFloat, msg_read as nm
        pos = [0.0, 0.0, 0.0]
        MSG_ReadPos(nm, pos)
        MSG_ReadFloat(nm)
        MSG_ReadFloat(nm)
    except Exception:
        return


def CL_ParseTEnt():
    try:
        from .common import MSG_ReadByte, msg_read as nm
        MSG_ReadByte(nm)
    except Exception:
        return


def CL_AddBeams():
    return


def CL_AddPlayerBeams():
    return


def CL_AddExplosions():
    return


def CL_AddLasers():
    return


def CL_ProcessSustain():
    return


def CL_AddTEnts():
    CL_AddBeams()
    CL_AddPlayerBeams()
    CL_AddExplosions()
    CL_AddLasers()
    CL_ProcessSustain()
