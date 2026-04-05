import random
import struct
from wrapper_qpy.decorators import va_args, va_args2, static_vars, TODO
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QEnums import ERROR_LVL


LinkEmptyFunctions(globals(), ["Con_Print", "Com_sprintf", "va", "FS_Gamedir", "CL_Drop", "CL_Shutdown", "SV_Shutdown",
                               "Sys_ConsoleOutput", "Sys_Error"])

MAXPRINTMSG = 4096
MAX_NUM_ARGVS = 50
MAX_QPATH = 64

com_argv = list()

realtime = 0

host_speeds = None
log_stats = None
developer = None
timescale = None
fixedtime = None
logfile_active = None
showtrace = None
dedicated = None

logfile = None

rd_target = 0
rd_buffer = None
rd_buffersize = 0
rd_flush = None

server_state = 0

# Message read buffer (global, used by MSG_Read* functions)
msg_read = {
    'data': bytearray(),
    'maxsize': 0,
    'cursize': 0,
    'readcount': 0,
    'allowoverflow': False,
    'overflowed': False,
}

# 162 pre-computed vertex normals for direction encoding
_bytedirs = [
    [-0.525731, 0.000000, 0.850651], [-0.442863, 0.238856, 0.864188],
    [-0.295242, 0.000000, 0.955423], [-0.309017, 0.500000, 0.809017],
    [-0.162460, 0.262866, 0.951056], [0.000000, 0.000000, 1.000000],
    [0.000000, 0.850651, 0.525731], [-0.147621, 0.716567, 0.681718],
    [0.147621, 0.716567, 0.681718], [0.000000, 0.525731, 0.850651],
    [0.309017, 0.500000, 0.809017], [0.525731, 0.000000, 0.850651],
    [0.295242, 0.000000, 0.955423], [0.442863, 0.238856, 0.864188],
    [0.162460, 0.262866, 0.951056], [-0.681718, 0.147621, 0.716567],
    [-0.809017, 0.309017, 0.500000], [-0.587785, 0.425325, 0.688191],
    [-0.850651, 0.525731, 0.000000], [-0.864188, 0.442863, 0.238856],
    [-0.716567, 0.681718, 0.147621], [-0.688191, 0.587785, 0.425325],
    [-0.500000, 0.809017, 0.309017], [-0.238856, 0.864188, 0.442863],
    [-0.425325, 0.688191, 0.587785], [-0.716567, 0.681718, -0.147621],
    [-0.500000, 0.809017, -0.309017], [-0.525731, 0.850651, 0.000000],
    [0.000000, 0.850651, -0.525731], [-0.238856, 0.864188, -0.442863],
    [0.000000, 0.955423, -0.295242], [-0.262866, 0.951056, -0.162460],
    [0.000000, 1.000000, 0.000000], [0.000000, 0.955423, 0.295242],
    [-0.262866, 0.951056, 0.162460], [0.238856, 0.864188, 0.442863],
    [0.262866, 0.951056, 0.162460], [0.500000, 0.809017, 0.309017],
    [0.238856, 0.864188, -0.442863], [0.262866, 0.951056, -0.162460],
    [0.500000, 0.809017, -0.309017], [0.850651, 0.525731, 0.000000],
    [0.716567, 0.681718, 0.147621], [0.716567, 0.681718, -0.147621],
    [0.525731, 0.850651, 0.000000], [0.425325, 0.688191, 0.587785],
    [0.864188, 0.442863, 0.238856], [0.688191, 0.587785, 0.425325],
    [0.809017, 0.309017, 0.500000], [0.681718, 0.147621, 0.716567],
    [0.587785, 0.425325, 0.688191], [0.955423, 0.295242, 0.000000],
    [1.000000, 0.000000, 0.000000], [0.951056, 0.162460, 0.262866],
    [0.850651, -0.525731, 0.000000], [0.955423, -0.295242, 0.000000],
    [0.864188, -0.442863, 0.238856], [0.951056, -0.162460, 0.262866],
    [0.809017, -0.309017, 0.500000], [0.681718, -0.147621, 0.716567],
    [0.850651, 0.000000, 0.525731], [0.864188, 0.442863, -0.238856],
    [0.809017, 0.309017, -0.500000], [0.951056, 0.162460, -0.262866],
    [0.525731, 0.000000, -0.850651], [0.681718, 0.147621, -0.716567],
    [0.681718, -0.147621, -0.716567], [0.850651, 0.000000, -0.525731],
    [0.809017, -0.309017, -0.500000], [0.864188, -0.442863, -0.238856],
    [0.951056, -0.162460, -0.262866], [0.147621, 0.716567, -0.681718],
    [0.309017, 0.500000, -0.809017], [0.425325, 0.688191, -0.587785],
    [0.442863, 0.238856, -0.864188], [0.587785, 0.425325, -0.688191],
    [0.688191, 0.587785, -0.425325], [-0.147621, 0.716567, -0.681718],
    [-0.309017, 0.500000, -0.809017], [0.000000, 0.525731, -0.850651],
    [-0.525731, 0.000000, -0.850651], [-0.442863, 0.238856, -0.864188],
    [-0.295242, 0.000000, -0.955423], [-0.162460, 0.262866, -0.951056],
    [0.000000, 0.000000, -1.000000], [0.295242, 0.000000, -0.955423],
    [0.162460, 0.262866, -0.951056], [-0.442863, -0.238856, -0.864188],
    [-0.309017, -0.500000, -0.809017], [-0.162460, -0.262866, -0.951056],
    [0.000000, -0.850651, -0.525731], [-0.147621, -0.716567, -0.681718],
    [0.147621, -0.716567, -0.681718], [0.000000, -0.525731, -0.850651],
    [0.309017, -0.500000, -0.809017], [0.442863, -0.238856, -0.864188],
    [0.162460, -0.262866, -0.951056], [0.238856, -0.864188, -0.442863],
    [0.500000, -0.809017, -0.309017], [0.425325, -0.688191, -0.587785],
    [0.716567, -0.681718, -0.147621], [0.688191, -0.587785, -0.425325],
    [0.587785, -0.425325, -0.688191], [0.000000, -0.955423, -0.295242],
    [0.000000, -1.000000, 0.000000], [0.262866, -0.951056, -0.162460],
    [0.000000, -0.850651, 0.525731], [0.000000, -0.955423, 0.295242],
    [0.238856, -0.864188, 0.442863], [0.262866, -0.951056, 0.162460],
    [0.500000, -0.809017, 0.309017], [0.716567, -0.681718, 0.147621],
    [0.525731, -0.850651, 0.000000], [-0.238856, -0.864188, -0.442863],
    [-0.500000, -0.809017, -0.309017], [-0.262866, -0.951056, -0.162460],
    [-0.850651, -0.525731, 0.000000], [-0.716567, -0.681718, -0.147621],
    [-0.716567, -0.681718, 0.147621], [-0.525731, -0.850651, 0.000000],
    [-0.500000, -0.809017, 0.309017], [-0.238856, -0.864188, 0.442863],
    [-0.262866, -0.951056, 0.162460], [-0.864188, -0.442863, 0.238856],
    [-0.809017, -0.309017, 0.500000], [-0.688191, -0.587785, 0.425325],
    [-0.681718, -0.147621, 0.716567], [-0.442863, -0.238856, 0.864188],
    [-0.587785, -0.425325, 0.688191], [-0.309017, -0.500000, 0.809017],
    [-0.147621, -0.716567, 0.681718], [-0.425325, -0.688191, 0.587785],
    [-0.162460, -0.262866, 0.951056], [0.442863, -0.238856, 0.864188],
    [0.162460, -0.262866, 0.951056], [0.309017, -0.500000, 0.809017],
    [0.147621, -0.716567, 0.681718], [0.000000, -0.525731, 0.850651],
    [0.425325, -0.688191, 0.587785], [0.587785, -0.425325, 0.688191],
    [0.688191, -0.587785, 0.425325], [-0.955423, 0.295242, 0.000000],
    [-0.951056, 0.162460, 0.262866], [-1.000000, 0.000000, 0.000000],
    [-0.850651, 0.000000, 0.525731], [-0.955423, -0.295242, 0.000000],
    [-0.951056, -0.162460, 0.262866], [-0.864188, 0.442863, -0.238856],
    [-0.951056, 0.162460, -0.262866], [-0.809017, 0.309017, -0.500000],
    [-0.864188, -0.442863, -0.238856], [-0.951056, -0.162460, -0.262866],
    [-0.809017, -0.309017, -0.500000], [-0.681718, 0.147621, -0.716567],
    [-0.681718, -0.147621, -0.716567], [-0.850651, 0.000000, -0.525731],
    [-0.688191, 0.587785, -0.425325], [-0.587785, 0.425325, -0.688191],
    [-0.425325, 0.688191, -0.587785], [-0.425325, -0.688191, -0.587785],
    [-0.587785, -0.425325, -0.688191], [-0.688191, -0.587785, -0.425325],
]

# Usercmd bit flags
_CM_ANGLE1  = (1 << 0)
_CM_ANGLE2  = (1 << 1)
_CM_ANGLE3  = (1 << 2)
_CM_FORWARD = (1 << 3)
_CM_SIDE    = (1 << 4)
_CM_UP      = (1 << 5)
_CM_BUTTONS = (1 << 6)
_CM_IMPULSE = (1 << 7)

# Entity update bit flags (subset needed for MSG_WriteDeltaEntity)
_U_ORIGIN1    = (1 << 9)
_U_ORIGIN2    = (1 << 10)
_U_ORIGIN3    = (1 << 11)
_U_ANGLE1     = (1 << 12)
_U_ANGLE2     = (1 << 14)
_U_ANGLE3     = (1 << 15)
_U_FRAME8     = (1 << 16)
_U_EVENT      = (1 << 17)
_U_REMOVE     = (1 << 18)
_U_MOREBITS1  = (1 << 7)
_U_MOREBITS2  = (1 << 23)
_U_MOREBITS3  = (1 << 30)
_U_FRAME16    = (1 << 29)
_U_MODEL      = (1 << 0)
_U_MODEL2     = (1 << 1)
_U_MODEL3     = (1 << 2)
_U_MODEL4     = (1 << 3)
_U_SKIN8      = (1 << 4)
_U_SKIN16     = (1 << 5)
_U_EFFECTS8   = (1 << 6)
_U_EFFECTS16  = (1 << 24)
_U_RENDERFX8  = (1 << 8)
_U_RENDERFX16 = (1 << 25)
_U_SOLID      = (1 << 13)
_U_SOUND      = (1 << 19)
_U_OLDORIGIN  = (1 << 20)
_U_NUMBER16   = (1 << 21)
_U_OLDORIGIN2 = (1 << 22)


def Com_BeginRedirect(target, buffer, buffersize, flush):
    global rd_target, rd_buffer, rd_buffersize, rd_flush
    if not target or not buffer or not buffersize or not flush:
        return
    rd_target, rd_buffer, rd_buffersize, rd_flush = target, buffer, buffersize, flush


def Com_EndRedirect():
    global rd_target, rd_buffer, rd_buffersize, rd_flush
    rd_flush(rd_target, rd_buffer)
    rd_target = 0
    rd_buffer = None
    rd_buffersize = 0
    rd_flush = None


@va_args
def Com_Printf(msg):
    global rd_buffer
    if rd_target > 0:
        if len(msg) + len(rd_buffer) > rd_buffersize -1:
            rd_flush(rd_target, rd_buffer)
        rd_buffer = msg
        return
    Con_Print(msg)
    Sys_ConsoleOutput(msg)
    if logfile_active is not None and logfile_active.value > 0:
        global logfile
        if logfile is None:
            name = Mutable()
            Com_sprintf(name, MAX_QPATH, "%s/qconsole.log", FS_Gamedir())
            logfile = open(name.GetValue(), "w")
        else:
            logfile.print(msg)
        if logfile_active.value > 1:
            logfile.flush()


def Com_DPrintf(msg):
    if developer is None or developer.value == 0:
        return
    Con_Print("%s", msg)



@va_args2(1)
@static_vars(recursive=False)
def Com_Error(code, msg):
    if Com_Error.recursive:
        Sys_Error("recursive error after: %s", msg)
    Com_Error.recursive = True
    if code == ERROR_LVL.ERR_DISCONNECT:
        CL_Drop()
        Com_Error.recursive = False
        # TODO: abortframe longjmp
    elif code == ERROR_LVL.ERR_DROP:
        Com_Printf("********************\nERROR: %s\n********************\n", msg)
        SV_Shutdown(va("Server crashed: %s\n", msg), False)
        CL_Drop()
        Com_Error.recursive = False
        # TODO: abortframe longjmp
    else:
        SV_Shutdown(va("Server fatal crashed: %s\n", msg), False)
        CL_Shutdown()
    global logfile
    if logfile is not None:
        logfile.flush()
        logfile.close()
        logfile = None
    Sys_Error("%s", msg)


def Com_Quit():
    SV_Shutdown("Server quit\n", False)
    CL_Shutdown()
    import sys
    sys.exit(0)


def Com_ServerState():
    return server_state


def Com_SetServerState(state):
    global server_state
    server_state = state


def _sz_get_space(buf, length):
    if buf['cursize'] + length > buf['maxsize']:
        if not buf['allowoverflow']:
            Com_Error(1, 'SZ_GetSpace: overflow without allowoverflow set')
        if length > buf['maxsize']:
            Com_Error(1, 'SZ_GetSpace: length > full buffer size')
        Com_Printf('SZ_GetSpace: overflow\n')
        buf['cursize'] = 0
        buf['overflowed'] = True
    pos = buf['cursize']
    buf['cursize'] += length
    return pos


def MSG_WriteChar(sb, c):
    pos = _sz_get_space(sb, 1)
    sb['data'][pos:pos+1] = struct.pack('b', c & 0xFF if c >= 0 else c)


def MSG_WriteByte(sb, c):
    pos = _sz_get_space(sb, 1)
    sb['data'][pos:pos+1] = bytes([c & 0xFF])


def MSG_WriteShort(sb, c):
    pos = _sz_get_space(sb, 2)
    sb['data'][pos:pos+2] = struct.pack('<h', c & 0xFFFF if c < 0x8000 else c - 0x10000)


def MSG_WriteLong(sb, c):
    pos = _sz_get_space(sb, 4)
    sb['data'][pos:pos+4] = struct.pack('<i', c)


def MSG_WriteFloat(sb, f):
    bits = struct.unpack('<i', struct.pack('<f', f))[0]
    MSG_WriteLong(sb, bits)


def MSG_WriteString(sb, s):
    if not s:
        SZ_Write(sb, b'\x00', 1)
    else:
        b = s.encode('latin-1', errors='replace') + b'\x00'
        SZ_Write(sb, b, len(b))


def MSG_WriteCoord(sb, f):
    MSG_WriteShort(sb, int(f * 8))


def MSG_WritePos(sb, pos):
    MSG_WriteShort(sb, int(pos[0] * 8))
    MSG_WriteShort(sb, int(pos[1] * 8))
    MSG_WriteShort(sb, int(pos[2] * 8))


def MSG_WriteAngle(sb, f):
    MSG_WriteByte(sb, int(f * 256 / 360) & 255)


def MSG_WriteAngle16(sb, f):
    MSG_WriteShort(sb, int(f * 65536 / 360) & 65535)


def MSG_WriteDeltaUsercmd(buf, _from, cmd):
    bits = 0
    if cmd.angles[0] != _from.angles[0]:    bits |= _CM_ANGLE1
    if cmd.angles[1] != _from.angles[1]:    bits |= _CM_ANGLE2
    if cmd.angles[2] != _from.angles[2]:    bits |= _CM_ANGLE3
    if cmd.forwardmove != _from.forwardmove: bits |= _CM_FORWARD
    if cmd.sidemove != _from.sidemove:       bits |= _CM_SIDE
    if cmd.upmove != _from.upmove:           bits |= _CM_UP
    if cmd.buttons != _from.buttons:         bits |= _CM_BUTTONS
    if cmd.impulse != _from.impulse:         bits |= _CM_IMPULSE
    MSG_WriteByte(buf, bits)
    if bits & _CM_ANGLE1:   MSG_WriteShort(buf, cmd.angles[0])
    if bits & _CM_ANGLE2:   MSG_WriteShort(buf, cmd.angles[1])
    if bits & _CM_ANGLE3:   MSG_WriteShort(buf, cmd.angles[2])
    if bits & _CM_FORWARD:  MSG_WriteShort(buf, cmd.forwardmove)
    if bits & _CM_SIDE:     MSG_WriteShort(buf, cmd.sidemove)
    if bits & _CM_UP:       MSG_WriteShort(buf, cmd.upmove)
    if bits & _CM_BUTTONS:  MSG_WriteByte(buf, cmd.buttons)
    if bits & _CM_IMPULSE:  MSG_WriteByte(buf, cmd.impulse)
    MSG_WriteByte(buf, cmd.msec)
    MSG_WriteByte(buf, cmd.lightlevel)


def MSG_WriteDir(sb, _dir):
    if not _dir:
        MSG_WriteByte(sb, 0)
        return
    bestd = 0.0
    best = 0
    for i, d in enumerate(_bytedirs):
        dot = _dir[0]*d[0] + _dir[1]*d[1] + _dir[2]*d[2]
        if dot > bestd:
            bestd = dot
            best = i
    MSG_WriteByte(sb, best)


def MSG_ReadDir(sb, _dir):
    b = MSG_ReadByte(sb)
    if b >= len(_bytedirs):
        Com_Error(1, 'MSG_ReadDir: out of range')
        return
    _dir[0] = _bytedirs[b][0]
    _dir[1] = _bytedirs[b][1]
    _dir[2] = _bytedirs[b][2]


def MSG_WriteDeltaEntity(_from, to, msg, force, newentity):
    if not to or not getattr(to, 'number', 0):
        return
    bits = 0
    if to.number >= 256:                             bits |= _U_NUMBER16
    if to.origin[0] != _from.origin[0]:             bits |= _U_ORIGIN1
    if to.origin[1] != _from.origin[1]:             bits |= _U_ORIGIN2
    if to.origin[2] != _from.origin[2]:             bits |= _U_ORIGIN3
    if to.angles[0] != _from.angles[0]:             bits |= _U_ANGLE1
    if to.angles[1] != _from.angles[1]:             bits |= _U_ANGLE2
    if to.angles[2] != _from.angles[2]:             bits |= _U_ANGLE3
    if to.modelindex != _from.modelindex:           bits |= _U_MODEL
    if getattr(to, 'modelindex2', 0) != getattr(_from, 'modelindex2', 0): bits |= _U_MODEL2
    if getattr(to, 'modelindex3', 0) != getattr(_from, 'modelindex3', 0): bits |= _U_MODEL3
    if getattr(to, 'modelindex4', 0) != getattr(_from, 'modelindex4', 0): bits |= _U_MODEL4
    fr = getattr(to, 'frame', 0)
    if fr != getattr(_from, 'frame', 0):
        if fr < 256: bits |= _U_FRAME8
        else:        bits |= _U_FRAME16
    skinnum = getattr(to, 'skinnum', 0)
    if skinnum != getattr(_from, 'skinnum', 0):
        if skinnum < 256:      bits |= _U_SKIN8
        elif skinnum < 0x10000: bits |= _U_SKIN16
        else:                  bits |= _U_SKIN8 | _U_SKIN16
    effects = getattr(to, 'effects', 0)
    if effects != getattr(_from, 'effects', 0):
        if effects < 256:    bits |= _U_EFFECTS8
        elif effects < 0x8000: bits |= _U_EFFECTS16
        else:                bits |= _U_EFFECTS8 | _U_EFFECTS16
    rfx = getattr(to, 'renderfx', 0)
    if rfx != getattr(_from, 'renderfx', 0):
        if rfx < 256:      bits |= _U_RENDERFX8
        elif rfx < 0x8000: bits |= _U_RENDERFX16
        else:              bits |= _U_RENDERFX8 | _U_RENDERFX16
    if getattr(to, 'solid', 0) != getattr(_from, 'solid', 0): bits |= _U_SOLID
    if getattr(to, 'event', 0):                               bits |= _U_EVENT
    if getattr(to, 'sound', 0) != getattr(_from, 'sound', 0): bits |= _U_SOUND
    if newentity or (rfx & 0x40):                             bits |= _U_OLDORIGIN
    if not bits and not force:
        return
    if bits & 0xff000000:   bits |= _U_MOREBITS3 | _U_MOREBITS2 | _U_MOREBITS1
    elif bits & 0x00ff0000: bits |= _U_MOREBITS2 | _U_MOREBITS1
    elif bits & 0x0000ff00: bits |= _U_MOREBITS1
    MSG_WriteByte(msg, bits & 255)
    if bits & 0xff000000:
        MSG_WriteByte(msg, (bits >> 8) & 255)
        MSG_WriteByte(msg, (bits >> 16) & 255)
        MSG_WriteByte(msg, (bits >> 24) & 255)
    elif bits & 0x00ff0000:
        MSG_WriteByte(msg, (bits >> 8) & 255)
        MSG_WriteByte(msg, (bits >> 16) & 255)
    elif bits & 0x0000ff00:
        MSG_WriteByte(msg, (bits >> 8) & 255)
    if bits & _U_NUMBER16: MSG_WriteShort(msg, to.number)
    else:                  MSG_WriteByte(msg, to.number)
    if bits & _U_MODEL:    MSG_WriteByte(msg, to.modelindex)
    if bits & _U_MODEL2:   MSG_WriteByte(msg, getattr(to, 'modelindex2', 0))
    if bits & _U_MODEL3:   MSG_WriteByte(msg, getattr(to, 'modelindex3', 0))
    if bits & _U_MODEL4:   MSG_WriteByte(msg, getattr(to, 'modelindex4', 0))
    if bits & _U_FRAME8:   MSG_WriteByte(msg, fr)
    if bits & _U_FRAME16:  MSG_WriteShort(msg, fr)
    if (bits & (_U_SKIN8 | _U_SKIN16)) == (_U_SKIN8 | _U_SKIN16):
        MSG_WriteLong(msg, skinnum)
    elif bits & _U_SKIN8:  MSG_WriteByte(msg, skinnum)
    elif bits & _U_SKIN16: MSG_WriteShort(msg, skinnum)
    if (bits & (_U_EFFECTS8 | _U_EFFECTS16)) == (_U_EFFECTS8 | _U_EFFECTS16):
        MSG_WriteLong(msg, effects)
    elif bits & _U_EFFECTS8:  MSG_WriteByte(msg, effects)
    elif bits & _U_EFFECTS16: MSG_WriteShort(msg, effects)
    if (bits & (_U_RENDERFX8 | _U_RENDERFX16)) == (_U_RENDERFX8 | _U_RENDERFX16):
        MSG_WriteLong(msg, rfx)
    elif bits & _U_RENDERFX8:  MSG_WriteByte(msg, rfx)
    elif bits & _U_RENDERFX16: MSG_WriteShort(msg, rfx)
    if bits & _U_ORIGIN1: MSG_WriteCoord(msg, to.origin[0])
    if bits & _U_ORIGIN2: MSG_WriteCoord(msg, to.origin[1])
    if bits & _U_ORIGIN3: MSG_WriteCoord(msg, to.origin[2])
    if bits & _U_ANGLE1:  MSG_WriteAngle(msg, to.angles[0])
    if bits & _U_ANGLE2:  MSG_WriteAngle(msg, to.angles[1])
    if bits & _U_ANGLE3:  MSG_WriteAngle(msg, to.angles[2])
    if bits & _U_OLDORIGIN:
        old = getattr(to, 'old_origin', to.origin)
        MSG_WriteCoord(msg, old[0])
        MSG_WriteCoord(msg, old[1])
        MSG_WriteCoord(msg, old[2])
    if bits & _U_SOUND: MSG_WriteByte(msg, getattr(to, 'sound', 0))
    if bits & _U_EVENT: MSG_WriteByte(msg, getattr(to, 'event', 0))
    if bits & _U_SOLID: MSG_WriteShort(msg, getattr(to, 'solid', 0))


def MSG_BeginReading(buf):
    buf['readcount'] = 0


def MSG_ReadChar(buf):
    if buf['readcount'] + 1 > buf['cursize']:
        buf['readcount'] += 1
        return -1
    c = buf['data'][buf['readcount']]
    buf['readcount'] += 1
    return c if c < 128 else c - 256


def MSG_ReadByte(buf):
    if buf['readcount'] + 1 > buf['cursize']:
        buf['readcount'] += 1
        return -1
    c = buf['data'][buf['readcount']]
    buf['readcount'] += 1
    return c


def MSG_ReadShort(buf):
    if buf['readcount'] + 2 > buf['cursize']:
        buf['readcount'] += 2
        return -1
    c = struct.unpack_from('<h', buf['data'], buf['readcount'])[0]
    buf['readcount'] += 2
    return c


def MSG_ReadLong(buf):
    if buf['readcount'] + 4 > buf['cursize']:
        buf['readcount'] += 4
        return -1
    c = struct.unpack_from('<i', buf['data'], buf['readcount'])[0]
    buf['readcount'] += 4
    return c


def MSG_ReadFloat(buf):
    if buf['readcount'] + 4 > buf['cursize']:
        buf['readcount'] += 4
        return -1.0
    f = struct.unpack_from('<f', buf['data'], buf['readcount'])[0]
    buf['readcount'] += 4
    return f


def MSG_ReadString(buf):
    result = []
    while True:
        c = MSG_ReadChar(buf)
        if c == -1 or c == 0:
            break
        result.append(chr(c))
        if len(result) >= 2047:
            break
    return ''.join(result)


def MSG_ReadStringLine(buf):
    result = []
    while True:
        c = MSG_ReadChar(buf)
        if c == -1 or c == 0 or c == ord('\n'):
            break
        result.append(chr(c))
        if len(result) >= 2047:
            break
    return ''.join(result)


def MSG_ReadCoord(buf):
    return MSG_ReadShort(buf) * (1.0 / 8)


def MSG_ReadPos(buf, pos):
    pos[0] = MSG_ReadShort(buf) * (1.0 / 8)
    pos[1] = MSG_ReadShort(buf) * (1.0 / 8)
    pos[2] = MSG_ReadShort(buf) * (1.0 / 8)


def MSG_ReadAngle(buf):
    return MSG_ReadChar(buf) * (360.0 / 256)


def MSG_ReadAngle16(buf):
    return MSG_ReadShort(buf) * (360.0 / 65536)


def MSG_ReadDeltaUsercmd(buf, _from, move):
    move.angles[:] = _from.angles[:]
    move.forwardmove = _from.forwardmove
    move.sidemove = _from.sidemove
    move.upmove = _from.upmove
    move.buttons = _from.buttons
    move.impulse = _from.impulse
    move.msec = _from.msec
    move.lightlevel = _from.lightlevel
    bits = MSG_ReadByte(buf)
    if bits & _CM_ANGLE1:   move.angles[0] = MSG_ReadShort(buf)
    if bits & _CM_ANGLE2:   move.angles[1] = MSG_ReadShort(buf)
    if bits & _CM_ANGLE3:   move.angles[2] = MSG_ReadShort(buf)
    if bits & _CM_FORWARD:  move.forwardmove = MSG_ReadShort(buf)
    if bits & _CM_SIDE:     move.sidemove = MSG_ReadShort(buf)
    if bits & _CM_UP:       move.upmove = MSG_ReadShort(buf)
    if bits & _CM_BUTTONS:  move.buttons = MSG_ReadByte(buf)
    if bits & _CM_IMPULSE:  move.impulse = MSG_ReadByte(buf)
    move.msec = MSG_ReadByte(buf)
    move.lightlevel = MSG_ReadByte(buf)


def MSG_ReadData(buf, data, length):
    for i in range(length):
        data[i] = MSG_ReadByte(buf)


def SZ_Init(buf, data, length):
    buf['data'] = bytearray(length) if data is None else bytearray(data[:length])
    buf['maxsize'] = length
    buf['cursize'] = 0
    buf['readcount'] = 0
    buf['allowoverflow'] = False
    buf['overflowed'] = False


def SZ_Clear(buf):
    buf['cursize'] = 0
    buf['overflowed'] = False


def SZ_GetSpace(buf, length):
    return _sz_get_space(buf, length)


def SZ_Write(buf, data, length):
    pos = _sz_get_space(buf, length)
    if isinstance(data, (bytes, bytearray)):
        buf['data'][pos:pos+length] = data[:length]
    else:
        buf['data'][pos:pos+length] = bytes(data[:length])


def SZ_Print(buf, data):
    if isinstance(data, str):
        data = data.encode('latin-1', errors='replace') + b'\x00'
    length = len(data)
    if buf['cursize'] and buf['data'][buf['cursize']-1] == 0:
        buf['cursize'] -= 1
    SZ_Write(buf, data, length)


def COM_CheckParm(parm):
    for i in range(1, len(com_argv)):
        if com_argv[i] == parm:
            return i
    return 0


def COM_Argc():
    return len(com_argv)


def COM_Argv(arg):
    if arg < 0 or arg >= len(com_argv):
        return ''
    return com_argv[arg]


def COM_ClearArgv(argc, argv):
    global com_argv
    if argc >= 0 and argc < len(com_argv):
        com_argv[argc] = ''


def COM_InitArgv(argc, argv):
    global com_argv
    com_argv.clear()
    for i in range(min(argc, MAX_NUM_ARGVS)):
        if isinstance(argv, (list, tuple)) and i < len(argv):
            com_argv.append(str(argv[i]) if argv[i] else '')
        else:
            com_argv.append('')


def COM_AddParm(parm):
    if len(com_argv) >= MAX_NUM_ARGVS:
        Com_Error(1, 'COM_AddParm: MAX_NUM_ARGVS')
        return
    com_argv.append(parm)


def memsearch(start, count, search):
    try:
        idx = start.index(search, 0, count)
        return idx
    except (ValueError, AttributeError):
        return -1


def CopyString(_in):
    return str(_in) if _in else ''


def Info_Print(s):
    if not s:
        return
    key = ''
    value = ''
    i = 0
    while i < len(s):
        if s[i] == '\\':
            i += 1
            key = ''
            while i < len(s) and s[i] != '\\':
                key += s[i]
                i += 1
            i += 1
            value = ''
            while i < len(s) and s[i] != '\\':
                value += s[i]
                i += 1
            Com_Printf('%-20s %s\n', key, value)
        else:
            i += 1


def Z_Free(ptr):
    return


def Z_Stats_f():
    Com_Printf('Zone memory stats not tracked in Python\n')


def Z_FreeTags(tag):
    return


def Z_TagMalloc(size, tag):
    return bytearray(size)


def Z_Malloc(size):
    return Z_TagMalloc(size, 0)


def COM_BlockSequenceCheckByte(base, length, sequence, challenge):
    from .crc import CRC_Block
    chkb = bytearray(base[:length]) + struct.pack('<i', sequence)
    crc = CRC_Block(bytes(chkb), len(chkb))
    crc ^= challenge
    return crc & 0xFF


def COM_BlockSequenceCRCByte(base, length, sequence):
    from .crc import CRC_Block
    chkb = bytearray(base[:length]) + struct.pack('<i', sequence)
    crc = CRC_Block(bytes(chkb), len(chkb))
    return crc & 0xFF


def frand():
    return random.random()


def crand():
    return random.uniform(-1.0, 1.0)


def Com_Error_f():
    from .cmd import Cmd_Argv
    Com_Error(1, Cmd_Argv(1))


def Qcommon_Init(argc, argv):
    """
    Initialize all engine subsystems.
    Called once at startup.
    """
    global host_speeds, log_stats, developer, timescale, fixedtime, logfile_active, showtrace, dedicated

    Com_Printf("====== Quake 2 Initializing ======\n\n")

    # Initialize memory
    # z_chain.next = z_chain.prev = &z_chain

    # Initialize basic subsystems first
    try:
        # Parse command line arguments
        com_argv.clear()
        for i in range(argc):
            if isinstance(argv, list):
                com_argv.append(argv[i])
            else:
                com_argv.append(str(argv[i]))

        # Initialize command buffer
        from .cmd import Cbuf_Init, Cbuf_AddText, Cbuf_Execute
        Cbuf_Init()

        # Initialize commands
        from .cmd import Cmd_Init, Cmd_AddCommand
        Cmd_Init()

        # Initialize console variables
        from .cvar import Cvar_Init, Cvar_Get
        Cvar_Init()

        # Initialize key binding system
        try:
            from .keys import Key_Init
            Key_Init()
        except:
            pass

        # Add early commands (before config)
        Cbuf_AddText("exec default.cfg\n")
        Cbuf_AddText("exec config.cfg\n")
        Cbuf_Execute()

        # Initialize filesystem
        from .files import FS_InitFilesystem
        FS_InitFilesystem()

        # Register cvars
        host_speeds = Cvar_Get("host_speeds", "0", 0)
        log_stats = Cvar_Get("log_stats", "0", 0)
        developer = Cvar_Get("developer", "0", 0)
        timescale = Cvar_Get("timescale", "1", 0)
        fixedtime = Cvar_Get("fixedtime", "0", 0)
        logfile_active = Cvar_Get("logfile", "0", 0)
        showtrace = Cvar_Get("showtrace", "0", 0)
        dedicated = Cvar_Get("dedicated", "0", 0)

        # Register version
        import sys
        version = "Quake2-Python 1.0"
        Cvar_Get("version", version, 0)

        # Register error command
        Cmd_AddCommand("error", Com_Error_f)

        # Initialize network
        try:
            from .net_chan import Netchan_Init
            Netchan_Init()
        except:
            pass

        # Initialize server
        try:
            from .sv_main import SV_Init
            SV_Init()
        except Exception as e:
            Com_Printf(f"Warning: SV_Init failed: {e}\n")

        # Initialize client
        try:
            from .cl_main import CL_Init
            CL_Init()
        except Exception as e:
            Com_Printf(f"Warning: CL_Init failed: {e}\n")

        # Default action: load first map
        try:
            Cbuf_AddText("d1\n")
            Cbuf_Execute()
        except:
            pass

        Com_Printf("====== Quake 2 Initialized ======\n\n")

    except Exception as e:
        Com_Error(0, f"Error during initialization: {e}")


def Qcommon_Frame(msec):
    """
    Main game loop frame.
    Called once per frame (~60 Hz).
    Handles both server and client frame updates.
    """
    global log_stats, fixedtime, timescale, showtrace, host_speeds

    # Apply timescale and fixed time
    if fixedtime and fixedtime.value:
        msec = int(fixedtime.value)
    elif timescale and timescale.value:
        msec = int(msec * timescale.value)
        if msec < 1:
            msec = 1

    try:
        # Process console input
        try:
            from .sys_win import Sys_ConsoleInput
            from .cmd import Cbuf_AddText, Cbuf_Execute
            s = Sys_ConsoleInput()
            if s:
                Cbuf_AddText(f"{s}\n")
            Cbuf_Execute()
        except:
            pass

        # Show trace statistics if enabled
        if showtrace and showtrace.value:
            Com_Printf("Trace statistics\n")

        # Time server frame
        time_before = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_before = Sys_Milliseconds()

        # Run server frame
        try:
            from .sv_main import SV_Frame
            SV_Frame(msec)
        except Exception as e:
            Com_Printf(f"Warning: SV_Frame error: {e}\n")

        time_between = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_between = Sys_Milliseconds()

        # Run client frame
        try:
            from .cl_main import CL_Frame
            CL_Frame(msec)
        except Exception as e:
            Com_Printf(f"Warning: CL_Frame error: {e}\n")

        time_after = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_after = Sys_Milliseconds()

            all_time = time_after - time_before
            sv_time = time_between - time_before
            cl_time = time_after - time_between

            Com_Printf(f"all:{all_time:3d}ms sv:{sv_time:3d}ms cl:{cl_time:3d}ms\n")

    except Exception as e:
        # On error, try to continue
        Com_Printf(f"Frame error: {e}\n")


def Qcommon_Shutdown():
    """
    Shut down all engine subsystems.
    Called once at exit.
    """
    global logfile

    try:
        from .sv_main import SV_Shutdown
        SV_Shutdown("Server shutdown", False)
    except:
        pass

    try:
        from .cl_main import CL_Shutdown
        CL_Shutdown()
    except:
        pass

    # Close logfile
    if logfile is not None:
        logfile.close()
        logfile = None

    Com_Printf("Quake 2 shutdown\n")


from .sys_win import Sys_ConsoleOutput, Sys_Error
from .console import Con_Print
from .q_shared import Com_sprintf, va
from .files import FS_Gamedir
from .cl_main import CL_Drop, CL_Shutdown
from .sv_main import SV_Shutdown
from .cvar import Cvar_Get