"""
q_shared.py - Quake 2 shared data types, constants, and utilities
Translated from q_shared.h and q_shared.c
"""

import math

# ===== Type Definitions =====

# Basic types
vec_t = float


class CVarT:
    """Represents a console variable."""
    __slots__ = ('name', 'string', 'latched_string', 'flags', 'modified', 'value', 'next')

    def __init__(self, name='', string='', flags=0):
        self.name = name
        self.string = string
        self.latched_string = None
        self.flags = flags
        self.modified = False
        self.value = 0.0
        self.next = None


class CPlaneT:
    """Collision plane."""
    __slots__ = ('normal', 'dist', 'type', 'signbits')

    def __init__(self):
        self.normal = [0.0, 0.0, 0.0]
        self.dist = 0.0
        self.type = 0  # PLANE_X, PLANE_Y, PLANE_Z, PLANE_ANYX, etc
        self.signbits = 0  # signx + (signy<<1) + (signz<<2)


class CModelT:
    """Collision model."""
    __slots__ = ('mins', 'maxs', 'origin', 'headnode')

    def __init__(self):
        self.mins = [0.0, 0.0, 0.0]
        self.maxs = [0.0, 0.0, 0.0]
        self.origin = [0.0, 0.0, 0.0]
        self.headnode = 0


class CSurfaceT:
    """Surface description."""
    __slots__ = ('name', 'flags', 'value')

    def __init__(self, name='', flags=0, value=0):
        self.name = name
        self.flags = flags
        self.value = value


class TraceT:
    """Result of a trace operation."""
    __slots__ = ('allsolid', 'startsolid', 'fraction', 'endpos', 'plane', 'surface', 'contents', 'ent')

    def __init__(self):
        self.allsolid = False
        self.startsolid = False
        self.fraction = 1.0
        self.endpos = [0.0, 0.0, 0.0]
        self.plane = CPlaneT()
        self.surface = None
        self.contents = 0
        self.ent = None


class PMoveStateT:
    """Player movement state (sent over network, must be bit-exact)."""
    __slots__ = ('pm_type', 'origin', 'velocity', 'pm_flags', 'pm_time', 'gravity', 'delta_angles')

    def __init__(self):
        self.pm_type = PM_NORMAL
        self.origin = [0, 0, 0]  # fixed point 12.3
        self.velocity = [0, 0, 0]  # fixed point 12.3
        self.pm_flags = 0
        self.pm_time = 0
        self.gravity = 800
        self.delta_angles = [0, 0, 0]


class UserCmdT:
    """Client input command sent to server."""
    __slots__ = ('msec', 'buttons', 'angles', 'forwardmove', 'sidemove', 'upmove', 'impulse', 'lightlevel')

    def __init__(self):
        self.msec = 0
        self.buttons = 0
        self.angles = [0, 0, 0]
        self.forwardmove = 0
        self.sidemove = 0
        self.upmove = 0
        self.impulse = 0
        self.lightlevel = 0


class PMoveT:
    """Player movement request and result."""
    __slots__ = ('s', 'cmd', 'snapinitial', 'numtouch', 'touchents', 'viewangles', 'viewheight',
                 'mins', 'maxs', 'groundentity', 'watertype', 'waterlevel', 'trace_func', 'pointcontents_func')

    def __init__(self):
        self.s = PMoveStateT()
        self.cmd = UserCmdT()
        self.snapinitial = False
        self.numtouch = 0
        self.touchents = [None] * 32
        self.viewangles = [0.0, 0.0, 0.0]
        self.viewheight = 0.0
        self.mins = [0.0, 0.0, 0.0]
        self.maxs = [0.0, 0.0, 0.0]
        self.groundentity = None
        self.watertype = 0
        self.waterlevel = 0
        self.trace_func = None  # callable(start, mins, maxs, end) -> TraceT
        self.pointcontents_func = None  # callable(point) -> int


# ===== Constants =====

# Angle indices
PITCH = 0
YAW = 1
ROLL = 2

# String limits
MAX_STRING_CHARS = 1024
MAX_STRING_TOKENS = 80
MAX_TOKEN_CHARS = 128
MAX_QPATH = 64
MAX_OSPATH = 128

# Per-level limits
MAX_CLIENTS = 256
MAX_EDICTS = 1024
MAX_LIGHTSTYLES = 256
MAX_MODELS = 256
MAX_SOUNDS = 256
MAX_IMAGES = 256
MAX_ITEMS = 256
MAX_GENERAL = MAX_CLIENTS * 2

# Game print levels
PRINT_LOW = 0
PRINT_MEDIUM = 1
PRINT_HIGH = 2
PRINT_CHAT = 3
PRINT_ALL = 0
PRINT_DEVELOPER = 1
PRINT_ALERT = 2

# Error levels
ERR_FATAL = 0
ERR_DROP = 1
ERR_DISCONNECT = 2

# Multicast modes
MULTICAST_ALL = 0
MULTICAST_PHS = 1
MULTICAST_PVS = 2
MULTICAST_ALL_R = 3
MULTICAST_PHS_R = 4
MULTICAST_PVS_R = 5

# Movement types
PM_NORMAL = 0
PM_SPECTATOR = 1
PM_DEAD = 2
PM_GIB = 3
PM_FREEZE = 4

# Player movement flags
PMF_DUCKED = 1
PMF_JUMP_HELD = 2
PMF_ON_GROUND = 4
PMF_TIME_WATERJUMP = 8
PMF_TIME_LAND = 16
PMF_TIME_TELEPORT = 32
PMF_NO_PREDICTION = 64

# Button bits
BUTTON_ATTACK = 1
BUTTON_USE = 2
BUTTON_ANY = 128

# Content flags (lower bits stronger, eat weaker)
CONTENTS_SOLID = 1
CONTENTS_WINDOW = 2
CONTENTS_AUX = 4
CONTENTS_LAVA = 8
CONTENTS_SLIME = 16
CONTENTS_WATER = 32
CONTENTS_MIST = 64
LAST_VISIBLE_CONTENTS = 64
CONTENTS_AREAPORTAL = 0x8000
CONTENTS_PLAYERCLIP = 0x10000
CONTENTS_MONSTERCLIP = 0x20000
CONTENTS_CURRENT_0 = 0x40000
CONTENTS_CURRENT_90 = 0x80000
CONTENTS_CURRENT_180 = 0x100000
CONTENTS_CURRENT_270 = 0x200000
CONTENTS_CURRENT_UP = 0x400000
CONTENTS_CURRENT_DOWN = 0x800000
CONTENTS_ORIGIN = 0x1000000
CONTENTS_MONSTER = 0x2000000
CONTENTS_DEADMONSTER = 0x4000000
CONTENTS_DETAIL = 0x8000000
CONTENTS_TRANSLUCENT = 0x10000000
CONTENTS_LADDER = 0x20000000

# Content masks
MASK_ALL = -1
MASK_SOLID = (CONTENTS_SOLID | CONTENTS_WINDOW)
MASK_PLAYERSOLID = (CONTENTS_SOLID | CONTENTS_PLAYERCLIP | CONTENTS_WINDOW | CONTENTS_MONSTER)
MASK_DEADSOLID = (CONTENTS_SOLID | CONTENTS_PLAYERCLIP | CONTENTS_WINDOW)
MASK_MONSTERSOLID = (CONTENTS_SOLID | CONTENTS_MONSTERCLIP | CONTENTS_WINDOW | CONTENTS_MONSTER)
MASK_WATER = (CONTENTS_WATER | CONTENTS_LAVA | CONTENTS_SLIME)
MASK_OPAQUE = (CONTENTS_SOLID | CONTENTS_SLIME | CONTENTS_LAVA)
MASK_SHOT = (CONTENTS_SOLID | CONTENTS_MONSTER | CONTENTS_WINDOW | CONTENTS_DEADMONSTER)
MASK_CURRENT = (CONTENTS_CURRENT_0 | CONTENTS_CURRENT_90 | CONTENTS_CURRENT_180 | CONTENTS_CURRENT_270 | CONTENTS_CURRENT_UP | CONTENTS_CURRENT_DOWN)

# Surface flags
SURF_LIGHT = 0x1
SURF_SLICK = 0x2
SURF_SKY = 0x4
SURF_WARP = 0x8
SURF_TRANS33 = 0x10
SURF_TRANS66 = 0x20
SURF_FLOWING = 0x40
SURF_NODRAW = 0x80

# Area types for BoxEdicts
AREA_SOLID = 1
AREA_TRIGGERS = 2

# Entity effects (effects handled on client side)
EF_ROTATE = 0x00000001
EF_GIB = 0x00000002
EF_BLASTER = 0x00000008
EF_ROCKET = 0x00000010
EF_GRENADE = 0x00000020
EF_HYPERBLASTER = 0x00000040
EF_BFG = 0x00000080
EF_COLOR_SHELL = 0x00000100
EF_POWERSCREEN = 0x00000200
EF_ANIM01 = 0x00000400
EF_ANIM23 = 0x00000800
EF_ANIM_ALL = 0x00001000
EF_ANIM_ALLFAST = 0x00002000
EF_FLIES = 0x00004000
EF_QUAD = 0x00008000
EF_PENT = 0x00010000
EF_TELEPORTER = 0x00020000
EF_FLAG1 = 0x00040000
EF_FLAG2 = 0x00080000
EF_IONRIPPER = 0x00100000
EF_GREENGIB = 0x00200000
EF_BLUEHYPERBLASTER = 0x00400000
EF_SPINNINGLIGHTS = 0x00800000
EF_PLASMA = 0x01000000
EF_TRAP = 0x02000000
EF_TRACKER = 0x04000000
EF_DOUBLE = 0x08000000
EF_SPHERETRANS = 0x10000000
EF_TAGTRAIL = 0x20000000
EF_HALF_DAMAGE = 0x40000000
EF_TRACKERTRAIL = 0x80000000

# Render flags
RF_MINLIGHT = 1
RF_VIEWERMODEL = 2
RF_WEAPONMODEL = 4
RF_FULLBRIGHT = 8
RF_DEPTHHACK = 16
RF_TRANSLUCENT = 32
RF_FRAMELERP = 64
RF_BEAM = 128
RF_CUSTOMSKIN = 256
RF_GLOW = 512
RF_SHELL_RED = 1024
RF_SHELL_GREEN = 2048
RF_SHELL_BLUE = 4096
RF_IR_VISIBLE = 0x00008000
RF_SHELL_DOUBLE = 0x00010000
RF_SHELL_HALF_DAM = 0x00020000
RF_USE_DISGUISE = 0x00040000

# Player state refdef flags
RDF_UNDERWATER = 1
RDF_NOWORLDMODEL = 2
RDF_IRGOGGLES = 4
RDF_UVGOGGLES = 8

# Muzzle flashes (player)
MZ_BLASTER = 0
MZ_MACHINEGUN = 1
MZ_SHOTGUN = 2
MZ_CHAINGUN1 = 3
MZ_CHAINGUN2 = 4
MZ_CHAINGUN3 = 5
MZ_RAILGUN = 6
MZ_ROCKET = 7
MZ_GRENADE = 8
MZ_LOGIN = 9
MZ_LOGOUT = 10
MZ_RESPAWN = 11
MZ_BFG = 12
MZ_SSHOTGUN = 13
MZ_HYPERBLASTER = 14
MZ_ITEMRESPAWN = 15
MZ_IONRIPPER = 16
MZ_BLUEHYPERBLASTER = 17
MZ_PHALANX = 18
MZ_SILENCED = 128
MZ_ETF_RIFLE = 30
MZ_UNUSED = 31
MZ_SHOTGUN2 = 32
MZ_HEATBEAM = 33
MZ_BLASTER2 = 34
MZ_TRACKER = 35
MZ_NUKE1 = 36
MZ_NUKE2 = 37
MZ_NUKE4 = 38
MZ_NUKE8 = 39

# CVAR flags
CVAR_ARCHIVE = 1
CVAR_USERINFO = 2
CVAR_SERVERINFO = 4
CVAR_NOSET = 8
CVAR_LATCH = 16

# Plane type constants
PLANE_X = 0
PLANE_Y = 1
PLANE_Z = 2
PLANE_ANYX = 3
PLANE_ANYY = 4
PLANE_ANYZ = 5

# ===== Math Constants and Utilities =====

M_PI = math.pi

# Global variables
vec3_origin = [0.0, 0.0, 0.0]

# ===== Inline Math Macros (as functions) =====

def dot_product(a, b):
    """DotProduct(x,y) - returns dot product"""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def vec_subtract(a, b, c):
    """VectorSubtract(a,b,c) - c = a - b"""
    c[0] = a[0] - b[0]
    c[1] = a[1] - b[1]
    c[2] = a[2] - b[2]


def vec_add(a, b, c):
    """VectorAdd(a,b,c) - c = a + b"""
    c[0] = a[0] + b[0]
    c[1] = a[1] + b[1]
    c[2] = a[2] + b[2]


def vec_copy(a, b):
    """VectorCopy(a,b) - b = a"""
    b[0] = a[0]
    b[1] = a[1]
    b[2] = a[2]


def vec_clear(a):
    """VectorClear(a) - a = [0,0,0]"""
    a[0] = 0.0
    a[1] = 0.0
    a[2] = 0.0


def vec_negate(a, b):
    """VectorNegate(a,b) - b = -a"""
    b[0] = -a[0]
    b[1] = -a[1]
    b[2] = -a[2]


def vec_set(v, x, y, z):
    """VectorSet(v, x, y, z) - v = [x, y, z]"""
    v[0] = x
    v[1] = y
    v[2] = z


# ===== Math Functions =====

def vec_ma(veca, scale, vecb, vecc):
    """VectorMA(veca, scale, vecb, vecc) - vecc = veca + scale*vecb"""
    vecc[0] = veca[0] + scale * vecb[0]
    vecc[1] = veca[1] + scale * vecb[1]
    vecc[2] = veca[2] + scale * vecb[2]


def vec_length(v):
    """VectorLength(v) - returns length of vector"""
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])


def vec_normalize(v):
    """VectorNormalize(v) - normalizes vector in place, returns original length"""
    length = vec_length(v)
    if length:
        inv_len = 1.0 / length
        v[0] *= inv_len
        v[1] *= inv_len
        v[2] *= inv_len
    return length


def vec_normalize2(v, out):
    """VectorNormalize2(v, out) - out = normalized v, returns original length"""
    length = vec_length(v)
    if length:
        inv_len = 1.0 / length
        out[0] = v[0] * inv_len
        out[1] = v[1] * inv_len
        out[2] = v[2] * inv_len
    else:
        out[0] = out[1] = out[2] = 0.0
    return length


def vec_inverse(v):
    """VectorInverse(v) - v = -v"""
    v[0] = -v[0]
    v[1] = -v[1]
    v[2] = -v[2]


def vec_scale(v_in, scale, v_out):
    """VectorScale(in, scale, out) - out = in * scale"""
    v_out[0] = v_in[0] * scale
    v_out[1] = v_in[1] * scale
    v_out[2] = v_in[2] * scale


def cross_product(v1, v2, cross):
    """CrossProduct(v1, v2, cross) - cross = v1 x v2"""
    cross[0] = v1[1]*v2[2] - v1[2]*v2[1]
    cross[1] = v1[2]*v2[0] - v1[0]*v2[2]
    cross[2] = v1[0]*v2[1] - v1[1]*v2[0]


def vec_compare(v1, v2):
    """VectorCompare(v1, v2) - returns 1 if vectors are equal, 0 otherwise"""
    if v1[0] != v2[0] or v1[1] != v2[1] or v1[2] != v2[2]:
        return 0
    return 1


def angle_vectors(angles, forward, right, up):
    """
    AngleVectors(angles, forward, right, up)
    Converts YAW/PITCH/ROLL angles to forward/right/up vectors
    """
    yaw_rad = math.radians(angles[YAW])
    pitch_rad = math.radians(angles[PITCH])
    roll_rad = math.radians(angles[ROLL])

    sin_yaw = math.sin(yaw_rad)
    cos_yaw = math.cos(yaw_rad)
    sin_pitch = math.sin(pitch_rad)
    cos_pitch = math.cos(pitch_rad)
    sin_roll = math.sin(roll_rad)
    cos_roll = math.cos(roll_rad)

    # Forward vector
    forward[0] = cos_pitch * cos_yaw
    forward[1] = cos_pitch * sin_yaw
    forward[2] = -sin_pitch

    # Right vector
    right[0] = (-sin_roll * sin_pitch * cos_yaw) + (cos_roll * sin_yaw)
    right[1] = (-sin_roll * sin_pitch * sin_yaw) + (-cos_roll * cos_yaw)
    right[2] = -sin_roll * cos_pitch

    # Up vector
    up[0] = (cos_roll * sin_pitch * cos_yaw) + (sin_roll * sin_yaw)
    up[1] = (cos_roll * sin_pitch * sin_yaw) + (-sin_roll * cos_yaw)
    up[2] = cos_roll * cos_pitch


def lerp_angle(a1, a2, frac):
    """LerpAngle(a1, a2, frac) - linear interpolation between angles"""
    if a2 - a1 > 180:
        a2 -= 360
    if a2 - a1 < -180:
        a2 += 360
    return a1 + frac * (a2 - a1)


def anglemod(a):
    """anglemod(a) - normalize angle to 0-360 range"""
    return (360.0 / 65536) * (int(a * (65536 / 360.0)) & 65535)


def clear_bounds(mins, maxs):
    """ClearBounds(mins, maxs) - clear bounding box"""
    mins[0] = mins[1] = mins[2] = 99999.0
    maxs[0] = maxs[1] = maxs[2] = -99999.0


def add_point_to_bounds(v, mins, maxs):
    """AddPointToBounds(v, mins, maxs) - expand bounding box to include point"""
    for i in range(3):
        if v[i] < mins[i]:
            mins[i] = v[i]
        if v[i] > maxs[i]:
            maxs[i] = v[i]


def q_log2(val):
    """q_log2(val) - returns log base 2 of val"""
    if val <= 0:
        return 0
    result = 0
    while val > 1:
        val >>= 1
        result += 1
    return result


def box_on_plane_side(emins, emaxs, plane):
    """BoxOnPlaneSide(emins, emaxs, plane) - returns side of plane box is on"""
    if plane.type < 3:  # PLANE_X, PLANE_Y, PLANE_Z
        if plane.dist <= emins[plane.type]:
            return 1
        elif plane.dist >= emaxs[plane.type]:
            return 2
        else:
            return 3
    else:
        # Arbitrary plane - test all 8 corners
        for i in range(3):
            if plane.normal[i] < 0:
                break

        dist1 = dot_product(plane.normal, emins) - plane.dist

        for i in range(3):
            if plane.normal[i] > 0:
                break

        dist2 = dot_product(plane.normal, emaxs) - plane.dist

        sides = 0
        if dist1 >= 0:
            sides = 1
        if dist2 < 0:
            sides |= 2

        return sides if sides else 3


# ===== String utilities =====

def com_skip_path(pathname):
    """COM_SkipPath(pathname) - returns pointer to filename part"""
    i = len(pathname) - 1
    while i >= 0 and pathname[i] not in ('/','\\'):
        i -= 1
    return pathname[i+1:] if i >= 0 else pathname


def com_strip_extension(in_str):
    """COM_StripExtension(in, out) - removes extension from pathname"""
    i = len(in_str) - 1
    while i >= 0 and in_str[i] != '.':
        i -= 1
    return in_str[:i] if i >= 0 else in_str


def com_file_base(in_str):
    """COM_FileBase(in, out) - extracts base filename without path or extension"""
    # Get just the filename
    s = com_skip_path(in_str)
    # Remove extension
    return com_strip_extension(s)


def com_file_path(in_str):
    """COM_FilePath(in, out) - extracts path part of pathname"""
    i = len(in_str) - 1
    while i >= 0 and in_str[i] not in ('/','\\'):
        i -= 1
    return in_str[:i+1] if i >= 0 else ''


def q_stricmp(s1, s2):
    """Q_stricmp(s1, s2) - case-insensitive string compare"""
    return -1 if s1.lower() < s2.lower() else (1 if s1.lower() > s2.lower() else 0)


# ===== Byte order utilities =====

def little_short(l):
    """LittleShort(l) - convert short to little endian"""
    return l & 0xFFFF


def big_short(l):
    """BigShort(l) - convert short to big endian (on x86)"""
    return ((l & 0xFF) << 8) | ((l >> 8) & 0xFF)


def little_long(l):
    """LittleLong(l) - convert long to little endian"""
    return l & 0xFFFFFFFF


def big_long(l):
    """BigLong(l) - convert long to big endian (on x86)"""
    return (((l) & 0xff) << 24) | (((l) & 0xff00) << 8) | (((l) & 0xff0000) >> 8) | (((l) >> 24) & 0xff)


def little_float(l):
    """LittleFloat(l) - no conversion needed on x86"""
    return l


def big_float(l):
    """BigFloat(l) - swap bytes (on x86)"""
    import struct
    return struct.unpack('<f', struct.pack('>f', l))[0]


# ===== Exception types =====

class QuakeError(Exception):
    """Base Quake error exception"""
    pass


class QuakeFatalError(QuakeError):
    """Fatal error - exit game"""
    pass


class QuakeDropError(QuakeError):
    """Drop error - disconnect from game but don't exit"""
    pass
