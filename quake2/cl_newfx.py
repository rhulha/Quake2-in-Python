import math
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

PITCH = 0
YAW = 1
ROLL = 2


def vectoangles2(value1, angles):
    if value1[1] == 0 and value1[0] == 0:
        yaw = 0
        pitch = 90 if value1[2] > 0 else 270
    else:
        if value1[0]:
            yaw = math.atan2(value1[1], value1[0]) * 180 / math.pi
        elif value1[1] > 0:
            yaw = 90
        else:
            yaw = 270
        if yaw < 0:
            yaw += 360
        forward = math.sqrt(value1[0]**2 + value1[1]**2)
        pitch = math.atan2(value1[2], forward) * 180 / math.pi
        if pitch < 0:
            pitch += 360
    angles[PITCH] = -pitch
    angles[YAW] = yaw
    angles[ROLL] = 0


def CL_Flashlight(ent, pos):
    return


def CL_ColorFlash(pos, ent, intensity, r, g, b):
    return


def CL_DebugTrail(start, end):
    return


def CL_SmokeTrail(start, end, colorStart, colorRun, spacing):
    return


def CL_ForceWall(start, end, color):
    return


def CL_FlameEffects(ent, origin):
    return


def CL_GenericParticleEffect(org, _dir, color, count, numcolors, dispread, alphavel):
    return


def CL_BubbleTrail2(start, end, dist):
    return


def CL_Heatbeam(start, forward):
    return


def CL_ParticleSteamEffect(org, _dir, color, count, magnitude):
    return


def CL_ParticleSteamEffect2(_self):
    return


def CL_TrackerTrail(start, end, particleColor):
    return


def CL_Tracker_Shell(origin):
    return


def CL_MonsterPlasma_Shell(origin):
    return


def CL_Widowbeamout(_self):
    return


def CL_Nukeblast(_self):
    return


def CL_WidowSplash(org):
    return


def CL_Tracker_Explode(origin):
    return


def CL_TagTrail(start, end, color):
    return


def CL_ColorExplosionParticles(org, color, run):
    return


def CL_ParticleSmokeEffect(org, _dir, color, count, magnitude):
    return


def CL_BlasterParticles2(org, _dir, color):
    return


def CL_BlasterTrail2(start, end):
    return
