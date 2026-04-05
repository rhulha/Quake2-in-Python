from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

_multicast = {'data': bytearray(), 'maxsize': 65536, 'cursize': 0,
              'readcount': 0, 'allowoverflow': True, 'overflowed': False}


def PF_Unicast(ent, reliable):
    return


def PF_dprintf(msg):
    try:
        from .common import Com_Printf
        Com_Printf('%s', msg)
    except Exception:
        print(msg, end='')


def PF_cprintf(ent, level, msg):
    try:
        from .common import Com_Printf
        Com_Printf('%s', msg)
    except Exception:
        print(msg, end='')


def PF_centerprintf(ent, msg):
    try:
        from .common import MSG_WriteByte, MSG_WriteString, SZ_Clear
        from .sv_send import SV_Multicast
        SZ_Clear(_multicast)
        MSG_WriteByte(_multicast, 51)
        MSG_WriteString(_multicast, msg)
        PF_Unicast(ent, True)
    except Exception:
        return


def PF_error(msg):
    try:
        from .common import Com_Error
        Com_Error(1, 'Game Error: %s' % msg)
    except Exception:
        raise RuntimeError('Game Error: %s' % msg)


def PF_setmodel(ent, name):
    if not name:
        return
    try:
        from .sv_init import SV_ModelIndex
        i = SV_ModelIndex(name)
        if hasattr(ent, 's'):
            ent.s.modelindex = i
        elif isinstance(ent, dict):
            ent.get('s', ent)['modelindex'] = i
    except Exception:
        return


def PF_Configstring(index, val):
    if val is None:
        val = ''
    try:
        from .sv_init import sv
        sv['configstrings'][index] = val
    except Exception:
        return


def PF_WriteChar(c):
    try:
        from .common import MSG_WriteChar
        MSG_WriteChar(_multicast, c)
    except Exception:
        return


def PF_WriteByte(c):
    try:
        from .common import MSG_WriteByte
        MSG_WriteByte(_multicast, c)
    except Exception:
        return


def PF_WriteShort(c):
    try:
        from .common import MSG_WriteShort
        MSG_WriteShort(_multicast, c)
    except Exception:
        return


def PF_WriteLong(c):
    try:
        from .common import MSG_WriteLong
        MSG_WriteLong(_multicast, c)
    except Exception:
        return


def PF_WriteFloat(f):
    try:
        from .common import MSG_WriteFloat
        MSG_WriteFloat(_multicast, f)
    except Exception:
        return


def PF_WriteString(s):
    try:
        from .common import MSG_WriteString
        MSG_WriteString(_multicast, s)
    except Exception:
        return


def PF_WritePos(pos):
    try:
        from .common import MSG_WritePos
        MSG_WritePos(_multicast, pos)
    except Exception:
        return


def PF_WriteDir(_dir):
    try:
        from .common import MSG_WriteDir
        MSG_WriteDir(_multicast, _dir)
    except Exception:
        return


def PF_WriteAngle(f):
    try:
        from .common import MSG_WriteAngle
        MSG_WriteAngle(_multicast, f)
    except Exception:
        return


def PF_inPVS(p1, p2):
    try:
        from .cmodel import (CM_PointLeafnum, CM_LeafCluster, CM_LeafArea,
                              CM_ClusterPVS, CM_AreasConnected)
        leafnum = CM_PointLeafnum(p1)
        cluster = CM_LeafCluster(leafnum)
        area1 = CM_LeafArea(leafnum)
        mask = CM_ClusterPVS(cluster)
        leafnum = CM_PointLeafnum(p2)
        cluster = CM_LeafCluster(leafnum)
        area2 = CM_LeafArea(leafnum)
        if mask and not (mask[cluster >> 3] & (1 << (cluster & 7))):
            return False
        if not CM_AreasConnected(area1, area2):
            return False
        return True
    except Exception:
        return True


def PF_inPHS(p1, p2):
    try:
        from .cmodel import (CM_PointLeafnum, CM_LeafCluster, CM_LeafArea,
                              CM_ClusterPHS, CM_AreasConnected)
        leafnum = CM_PointLeafnum(p1)
        cluster = CM_LeafCluster(leafnum)
        area1 = CM_LeafArea(leafnum)
        mask = CM_ClusterPHS(cluster)
        leafnum = CM_PointLeafnum(p2)
        cluster = CM_LeafCluster(leafnum)
        area2 = CM_LeafArea(leafnum)
        if mask and not (mask[cluster >> 3] & (1 << (cluster & 7))):
            return False
        if not CM_AreasConnected(area1, area2):
            return False
        return True
    except Exception:
        return True


def PF_StartSound(entity, channel, sound_num, volume, attentuation, timeofs):
    try:
        from .sv_send import SV_StartSound
        SV_StartSound(None, entity, channel, sound_num, volume, attentuation, timeofs)
    except Exception:
        return


def SV_ShutdownGameProgs():
    return


def SV_InitGameProgs():
    return
