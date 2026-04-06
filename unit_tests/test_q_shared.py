"""
Unit tests for qcommon/q_shared.py
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qcommon import q_shared
from qcommon.q_shared import (
    CVarT, CPlaneT, CModelT, CSurfaceT, TraceT, PMoveStateT, UserCmdT, PMoveT,
    dot_product, vec_subtract, vec_add, vec_copy, vec_clear, vec_negate, vec_set,
    vec_ma, vec_length, vec_normalize, vec_normalize2, vec_inverse, vec_scale,
    cross_product, vec_compare,
    angle_vectors, lerp_angle, anglemod,
    clear_bounds, add_point_to_bounds,
    q_log2, box_on_plane_side,
    com_skip_path, com_strip_extension, com_file_base, com_file_path, q_stricmp,
    little_short, big_short, little_long, big_long, big_float,
    QuakeError, QuakeFatalError, QuakeDropError,
    PM_NORMAL, CVAR_ARCHIVE, CONTENTS_SOLID, CONTENTS_WINDOW, MASK_SOLID,
)

EPS = 1e-5


# ===== Classes =====

def test_cvar_t_defaults():
    c = CVarT()
    assert c.name == ''
    assert c.string == ''
    assert c.flags == 0
    assert c.modified is False
    assert c.value == 0.0
    assert c.next is None
    assert c.latched_string is None


def test_cvar_t_init():
    c = CVarT('sv_maxvelocity', '2000', CVAR_ARCHIVE)
    assert c.name == 'sv_maxvelocity'
    assert c.string == '2000'
    assert c.flags == CVAR_ARCHIVE


def test_cplane_t_defaults():
    p = CPlaneT()
    assert p.normal == [0.0, 0.0, 0.0]
    assert p.dist == 0.0
    assert p.type == 0
    assert p.signbits == 0


def test_cmodel_t_defaults():
    m = CModelT()
    assert m.mins == [0.0, 0.0, 0.0]
    assert m.maxs == [0.0, 0.0, 0.0]
    assert m.origin == [0.0, 0.0, 0.0]
    assert m.headnode == 0


def test_csurface_t_defaults():
    s = CSurfaceT()
    assert s.name == ''
    assert s.flags == 0
    assert s.value == 0


def test_csurface_t_init():
    s = CSurfaceT('sky', 0x4, 99)
    assert s.name == 'sky'
    assert s.flags == 0x4
    assert s.value == 99


def test_trace_t_defaults():
    t = TraceT()
    assert t.allsolid is False
    assert t.startsolid is False
    assert t.fraction == 1.0
    assert t.endpos == [0.0, 0.0, 0.0]
    assert t.contents == 0
    assert t.ent is None
    assert t.surface is None
    assert isinstance(t.plane, CPlaneT)


def test_pmove_state_t_defaults():
    p = PMoveStateT()
    assert p.pm_type == PM_NORMAL
    assert p.origin == [0, 0, 0]
    assert p.velocity == [0, 0, 0]
    assert p.gravity == 800


def test_usercmd_t_defaults():
    u = UserCmdT()
    assert u.msec == 0
    assert u.buttons == 0
    assert u.angles == [0, 0, 0]
    assert u.forwardmove == 0
    assert u.sidemove == 0
    assert u.upmove == 0


def test_pmove_t_defaults():
    p = PMoveT()
    assert isinstance(p.s, PMoveStateT)
    assert isinstance(p.cmd, UserCmdT)
    assert p.snapinitial is False
    assert p.numtouch == 0
    assert len(p.touchents) == 32
    assert p.groundentity is None
    assert p.trace_func is None
    assert p.pointcontents_func is None


# ===== Vector math =====

def test_dot_product():
    assert dot_product([1, 0, 0], [1, 0, 0]) == 1.0
    assert dot_product([1, 0, 0], [0, 1, 0]) == 0.0
    assert dot_product([1, 2, 3], [4, 5, 6]) == 32.0


def test_vec_subtract():
    c = [0.0, 0.0, 0.0]
    vec_subtract([5, 3, 1], [2, 1, 0], c)
    assert c == [3.0, 2.0, 1.0]


def test_vec_add():
    c = [0.0, 0.0, 0.0]
    vec_add([1, 2, 3], [4, 5, 6], c)
    assert c == [5.0, 7.0, 9.0]


def test_vec_copy():
    b = [0.0, 0.0, 0.0]
    vec_copy([7, 8, 9], b)
    assert b == [7, 8, 9]


def test_vec_clear():
    a = [1.0, 2.0, 3.0]
    vec_clear(a)
    assert a == [0.0, 0.0, 0.0]


def test_vec_negate():
    b = [0.0, 0.0, 0.0]
    vec_negate([1.0, -2.0, 3.0], b)
    assert b == [-1.0, 2.0, -3.0]


def test_vec_set():
    v = [0.0, 0.0, 0.0]
    vec_set(v, 1.0, 2.0, 3.0)
    assert v == [1.0, 2.0, 3.0]


def test_vec_ma():
    out = [0.0, 0.0, 0.0]
    vec_ma([1, 1, 1], 2.0, [3, 4, 5], out)
    assert out == [7.0, 9.0, 11.0]


def test_vec_length():
    assert abs(vec_length([3.0, 4.0, 0.0]) - 5.0) < EPS
    assert abs(vec_length([0.0, 0.0, 0.0])) < EPS


def test_vec_normalize():
    v = [3.0, 0.0, 0.0]
    length = vec_normalize(v)
    assert abs(length - 3.0) < EPS
    assert abs(v[0] - 1.0) < EPS
    assert abs(v[1]) < EPS
    assert abs(v[2]) < EPS


def test_vec_normalize_zero():
    v = [0.0, 0.0, 0.0]
    length = vec_normalize(v)
    assert length == 0.0
    assert v == [0.0, 0.0, 0.0]


def test_vec_normalize2():
    v = [0.0, 6.0, 0.0]
    out = [0.0, 0.0, 0.0]
    length = vec_normalize2(v, out)
    assert abs(length - 6.0) < EPS
    assert abs(out[1] - 1.0) < EPS
    assert out[0] == 0.0 and out[2] == 0.0


def test_vec_normalize2_zero():
    out = [1.0, 1.0, 1.0]
    vec_normalize2([0.0, 0.0, 0.0], out)
    assert out == [0.0, 0.0, 0.0]


def test_vec_inverse():
    v = [1.0, -2.0, 3.0]
    vec_inverse(v)
    assert v == [-1.0, 2.0, -3.0]


def test_vec_scale():
    out = [0.0, 0.0, 0.0]
    vec_scale([1.0, 2.0, 3.0], 3.0, out)
    assert out == [3.0, 6.0, 9.0]


def test_cross_product():
    cross = [0.0, 0.0, 0.0]
    cross_product([1, 0, 0], [0, 1, 0], cross)
    assert abs(cross[0]) < EPS
    assert abs(cross[1]) < EPS
    assert abs(cross[2] - 1.0) < EPS


def test_cross_product_anticommutative():
    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0]
    c1 = [0.0, 0.0, 0.0]
    c2 = [0.0, 0.0, 0.0]
    cross_product(a, b, c1)
    cross_product(b, a, c2)
    for i in range(3):
        assert abs(c1[i] + c2[i]) < EPS


def test_vec_compare_equal():
    assert vec_compare([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1


def test_vec_compare_not_equal():
    assert vec_compare([1.0, 2.0, 3.0], [1.0, 2.0, 4.0]) == 0


# ===== Angle functions =====

def test_angle_vectors_forward_east():
    fwd = [0.0, 0.0, 0.0]
    right = [0.0, 0.0, 0.0]
    up = [0.0, 0.0, 0.0]
    # pitch=0, yaw=0, roll=0 -> forward points along +X
    angle_vectors([0.0, 0.0, 0.0], fwd, right, up)
    assert abs(fwd[0] - 1.0) < EPS
    assert abs(fwd[1]) < EPS
    assert abs(fwd[2]) < EPS


def test_angle_vectors_up():
    fwd = [0.0, 0.0, 0.0]
    right = [0.0, 0.0, 0.0]
    up = [0.0, 0.0, 0.0]
    # pitch=-90 -> forward points straight up (+Z)
    angle_vectors([-90.0, 0.0, 0.0], fwd, right, up)
    assert abs(fwd[2] - 1.0) < EPS


def test_lerp_angle_basic():
    result = lerp_angle(0.0, 90.0, 0.5)
    assert abs(result - 45.0) < EPS


def test_lerp_angle_wrap_forward():
    # 350 -> 10 wraps correctly, producing ~0 at frac=0.5
    result = lerp_angle(350.0, 10.0, 0.5)
    assert abs(result - 360.0) < EPS or abs(result - 0.0) < EPS or abs(result - 0.0) < 1.0


def test_lerp_angle_wrap_backward():
    result = lerp_angle(10.0, 350.0, 0.5)
    assert abs(result - 0.0) < 1.0


def test_lerp_angle_no_wrap():
    result = lerp_angle(45.0, 135.0, 0.25)
    assert abs(result - 67.5) < EPS


@pytest.mark.parametrize(
    'value, expected',
    [
        (90.0, 90.0),
        (0.0, 0.0),
        (-90.0, 270.0),
        (450.0, 90.0),
    ],
)
def test_anglemod_cases(value, expected):
    result = anglemod(value)
    assert abs(result - expected) < 0.1


# ===== Bounding box =====

def test_clear_bounds():
    mins = [0.0, 0.0, 0.0]
    maxs = [0.0, 0.0, 0.0]
    clear_bounds(mins, maxs)
    for i in range(3):
        assert mins[i] == 99999.0
        assert maxs[i] == -99999.0


def test_add_point_to_bounds():
    mins = [99999.0, 99999.0, 99999.0]
    maxs = [-99999.0, -99999.0, -99999.0]
    add_point_to_bounds([1.0, 2.0, 3.0], mins, maxs)
    assert mins == [1.0, 2.0, 3.0]
    assert maxs == [1.0, 2.0, 3.0]


def test_add_point_to_bounds_expands():
    mins = [99999.0, 99999.0, 99999.0]
    maxs = [-99999.0, -99999.0, -99999.0]
    add_point_to_bounds([1.0, 2.0, 3.0], mins, maxs)
    add_point_to_bounds([-1.0, 5.0, 0.0], mins, maxs)
    assert mins == [-1.0, 2.0, 0.0]
    assert maxs == [1.0, 5.0, 3.0]


# ===== Integer math =====

@pytest.mark.parametrize(
    'value, expected',
    [
        (1, 0),
        (2, 1),
        (4, 2),
        (8, 3),
        (256, 8),
        (0, 0),
        (-5, 0),
    ],
)
def test_q_log2_cases(value, expected):
    assert q_log2(value) == expected


def test_box_on_plane_side_front():
    plane = CPlaneT()
    plane.type = 0  # PLANE_X
    plane.normal = [1.0, 0.0, 0.0]
    plane.dist = 5.0
    # box entirely in front (mins[x] > dist)
    side = box_on_plane_side([10.0, 0.0, 0.0], [20.0, 1.0, 1.0], plane)
    assert side == 1


def test_box_on_plane_side_back():
    plane = CPlaneT()
    plane.type = 0  # PLANE_X
    plane.normal = [1.0, 0.0, 0.0]
    plane.dist = 50.0
    # box entirely behind (maxs[x] < dist)
    side = box_on_plane_side([0.0, 0.0, 0.0], [10.0, 1.0, 1.0], plane)
    assert side == 2


def test_box_on_plane_side_spanning():
    plane = CPlaneT()
    plane.type = 0  # PLANE_X
    plane.normal = [1.0, 0.0, 0.0]
    plane.dist = 5.0
    # box spanning the plane
    side = box_on_plane_side([0.0, 0.0, 0.0], [10.0, 1.0, 1.0], plane)
    assert side == 3


def test_box_on_plane_side_arbitrary_positive_normal_front():
    plane = CPlaneT()
    plane.type = 3  # non-axial plane path
    plane.normal = [1.0, 1.0, 1.0]
    plane.dist = 1.0
    side = box_on_plane_side([2.0, 2.0, 2.0], [4.0, 4.0, 4.0], plane)
    assert side == 1


def test_box_on_plane_side_arbitrary_negative_normal_back():
    plane = CPlaneT()
    plane.type = 4  # non-axial plane path
    plane.normal = [-1.0, -1.0, -1.0]
    plane.dist = 1.0
    side = box_on_plane_side([0.0, 0.0, 0.0], [1.0, 1.0, 1.0], plane)
    assert side == 2


# ===== String utilities =====

@pytest.mark.parametrize(
    'value, expected',
    [
        ('maps/base1.bsp', 'base1.bsp'),
        ('maps\\base1.bsp', 'base1.bsp'),
        ('base1.bsp', 'base1.bsp'),
    ],
)
def test_com_skip_path_cases(value, expected):
    assert com_skip_path(value) == expected


@pytest.mark.parametrize(
    'value, expected',
    [
        ('base1.bsp', 'base1'),
        ('base1', 'base1'),
        ('pak0.backup.pak', 'pak0.backup'),
    ],
)
def test_com_strip_extension_cases(value, expected):
    assert com_strip_extension(value) == expected


@pytest.mark.parametrize(
    'value, expected',
    [
        ('maps/base1.bsp', 'base1'),
        ('base1.bsp', 'base1'),
        ('textures/metal.wall.tga', 'metal.wall'),
    ],
)
def test_com_file_base_cases(value, expected):
    assert com_file_base(value) == expected


def test_com_file_path_with_slash():
    result = com_file_path('maps/base1.bsp')
    assert result == 'maps/'


def test_com_file_path_no_path():
    result = com_file_path('base1.bsp')
    assert result == ''


def test_com_file_path_backslash():
    result = com_file_path('maps\\base1.bsp')
    assert result == 'maps\\'


@pytest.mark.parametrize(
    'left, right, expected',
    [
        ('Hello', 'hello', 0),
        ('ABC', 'abc', 0),
        ('a', 'b', -1),
        ('b', 'a', 1),
    ],
)
def test_q_stricmp_cases(left, right, expected):
    assert q_stricmp(left, right) == expected


# ===== Byte order utilities =====

def test_little_short():
    assert little_short(0x1234) == 0x1234
    assert little_short(0xFFFF) == 0xFFFF


def test_big_short():
    assert big_short(0x1234) == 0x3412


def test_little_long():
    assert little_long(0x12345678) == 0x12345678


def test_big_long():
    assert big_long(0x12345678) == 0x78563412


def test_little_float():
    assert q_shared.little_float(3.14) == 3.14


def test_big_float_roundtrip():
    val = 1.0
    swapped = big_float(val)
    # swapping twice should give back the original
    assert abs(big_float(swapped) - val) < EPS


def test_big_float_negative_roundtrip():
    val = -123.25
    swapped = big_float(val)
    assert abs(big_float(swapped) - val) < EPS


# ===== Exceptions =====

@pytest.mark.parametrize('exc_type, message', [
    (QuakeError, 'test'),
    (QuakeFatalError, 'fatal'),
    (QuakeDropError, 'drop'),
])
def test_quake_error_hierarchy(exc_type, message):
    with pytest.raises(QuakeError):
        raise exc_type(message)


# ===== Constants sanity checks =====

def test_mask_solid_definition():
    assert MASK_SOLID == (CONTENTS_SOLID | CONTENTS_WINDOW)


def test_pm_normal_is_zero():
    assert PM_NORMAL == 0
