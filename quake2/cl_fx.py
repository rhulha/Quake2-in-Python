from wrapper_qpy.linker import LinkEmptyFunctions
import math

LinkEmptyFunctions(globals(), [])

_dlights = []
_particles = []
_lightstyles = []


def CL_ClearLightStyles():
    global _lightstyles
    _lightstyles = [None] * 256


def CL_RunLightStyles():
    return


def CL_SetLightstyle():
    return


def CL_AddLightStyles():
    return


def CL_ClearDlights():
    global _dlights
    _dlights = []


def CL_AllocDlight(key):
    dl = {'key': key, 'origin': [0.0, 0.0, 0.0], 'radius': 0.0,
          'minlight': 0.0, 'die': 0.0, 'color': [0.0, 0.0, 0.0]}
    _dlights.append(dl)
    return dl


def CL_NewDlight(key, x, y, z, radius, time):
    dl = CL_AllocDlight(key)
    dl['origin'] = [x, y, z]
    dl['radius'] = radius
    dl['die'] = time


def CL_RunDLights():
    return


def CL_ParseMuzzleFlash():
    try:
        from .common import MSG_ReadShort, MSG_ReadByte, msg_read as net_message
        MSG_ReadShort(net_message)
        MSG_ReadByte(net_message)
    except Exception:
        return


def CL_ParseMuzzleFlash2():
    try:
        from .common import MSG_ReadShort, MSG_ReadByte, msg_read as net_message
        MSG_ReadShort(net_message)
        MSG_ReadByte(net_message)
    except Exception:
        return


def CL_AddDLights():
    return


def CL_ClearParticles():
    global _particles
    _particles = []


def CL_ParticleEffect(org, _dir, color, count):
    return


def CL_ParticleEffect2(org, _dir, color, count):
    return


def CL_ParticleEffect3(org, _dir, color, count):
    return


def CL_TeleporterParticles(ent):
    return


def CL_LogoutEffect(org, type):
    return


def CL_ItemRespawnParticles(org):
    return


def CL_ExplosionParticles(org):
    return


def CL_BigTeleportParticles(org):
    return


def CL_BlasterParticles(org, _dir):
    return


def CL_BlasterTrail(start, end):
    return


def CL_QuadTrail(start, end):
    return


def CL_FlagTrail(start, end, color):
    return


def CL_DiminishingTrail(start, end, old, flags):
    return


def MakeNormalVectors(forward, right, up):
    right[1] = -forward[0]
    right[2] = forward[1]
    right[0] = forward[2]
    d = right[0]*forward[0] + right[1]*forward[1] + right[2]*forward[2]
    for i in range(3):
        right[i] -= d * forward[i]
    length = math.sqrt(right[0]**2 + right[1]**2 + right[2]**2)
    if length:
        for i in range(3):
            right[i] /= length
    up[0] = right[1]*forward[2] - right[2]*forward[1]
    up[1] = right[2]*forward[0] - right[0]*forward[2]
    up[2] = right[0]*forward[1] - right[1]*forward[0]


def CL_RocketTrail(start, end, old):
    return


def CL_RailTrail(start, end):
    return


def CL_IonripperTrail(start, ent):
    return


def CL_BubbleTrail(start, end):
    return


def CL_FlyParticles(origin, count):
    return


def CL_FlyEffect(ent, origin):
    return


def CL_BfgParticles(ent):
    return


def CL_TrapParticles(ent):
    return


def CL_BFGExplosionParticles(org):
    return


def CL_TeleportParticles(org):
    return


def CL_AddParticles():
    return


def CL_EntityEvent(ent):
    return


def CL_ClearEffects():
    CL_ClearParticles()
    CL_ClearDlights()
    CL_ClearLightStyles()
