"""
Unit tests for qcommon/mathlib.py
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qcommon import q_shared
from qcommon.mathlib import (
    rotate_point_around_vector,
    perpendicular_vector,
    project_point_on_plane,
    r_concat_rotations,
    r_concat_transforms,
)

EPS = 1e-5


# ===== rotate_point_around_vector =====

def test_rotate_point_around_vector_360():
    dst = [0.0, 0.0, 0.0]
    point = [1.0, 0.0, 0.0]
    axis = [0.0, 0.0, 1.0]
    rotate_point_around_vector(dst, axis, point, 360.0)
    assert abs(dst[0] - 1.0) < EPS
    assert abs(dst[1]) < EPS
    assert abs(dst[2]) < EPS


def test_rotate_point_around_vector_90_z():
    dst = [0.0, 0.0, 0.0]
    # Rotate [1,0,0] 90 degrees around Z -> [0,1,0]
    rotate_point_around_vector(dst, [0.0, 0.0, 1.0], [1.0, 0.0, 0.0], 90.0)
    assert abs(dst[0]) < EPS
    assert abs(dst[1] - 1.0) < EPS
    assert abs(dst[2]) < EPS


def test_rotate_point_around_vector_90_x():
    dst = [0.0, 0.0, 0.0]
    # Rotate [0,1,0] 90 degrees around X -> [0,0,1]
    rotate_point_around_vector(dst, [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], 90.0)
    assert abs(dst[0]) < EPS
    assert abs(dst[1]) < EPS
    assert abs(dst[2] - 1.0) < EPS


def test_rotate_point_around_vector_preserves_length():
    dst = [0.0, 0.0, 0.0]
    point = [3.0, 4.0, 0.0]
    original_len = q_shared.vec_length(point)
    rotate_point_around_vector(dst, [0.0, 0.0, 1.0], point, 45.0)
    rotated_len = q_shared.vec_length(dst)
    assert abs(rotated_len - original_len) < EPS


def test_rotate_point_around_vector_180():
    dst = [0.0, 0.0, 0.0]
    # Rotate [1,0,0] 180 degrees around Z -> [-1,0,0]
    rotate_point_around_vector(dst, [0.0, 0.0, 1.0], [1.0, 0.0, 0.0], 180.0)
    assert abs(dst[0] + 1.0) < EPS
    assert abs(dst[1]) < EPS
    assert abs(dst[2]) < EPS


def test_rotate_point_on_axis_unchanged():
    dst = [0.0, 0.0, 0.0]
    # Rotating a point that lies along the axis should not change it
    rotate_point_around_vector(dst, [0.0, 0.0, 1.0], [0.0, 0.0, 5.0], 90.0)
    assert abs(dst[0]) < EPS
    assert abs(dst[1]) < EPS
    assert abs(dst[2] - 5.0) < EPS


# ===== perpendicular_vector =====

def test_perpendicular_vector_is_perpendicular_x():
    src = [1.0, 0.0, 0.0]
    dst = [0.0, 0.0, 0.0]
    perpendicular_vector(dst, src)
    assert abs(q_shared.dot_product(src, dst)) < EPS


def test_perpendicular_vector_is_perpendicular_y():
    src = [0.0, 1.0, 0.0]
    dst = [0.0, 0.0, 0.0]
    perpendicular_vector(dst, src)
    assert abs(q_shared.dot_product(src, dst)) < EPS


def test_perpendicular_vector_is_perpendicular_arbitrary():
    src = [1.0, 2.0, 3.0]
    q_shared.vec_normalize(src)
    dst = [0.0, 0.0, 0.0]
    perpendicular_vector(dst, src)
    assert abs(q_shared.dot_product(src, dst)) < EPS


def test_perpendicular_vector_is_unit():
    src = [0.0, 0.0, 1.0]
    dst = [0.0, 0.0, 0.0]
    perpendicular_vector(dst, src)
    assert abs(q_shared.vec_length(dst) - 1.0) < EPS


# ===== project_point_on_plane =====

def test_project_point_on_plane_xy():
    # Normal = Z-axis; point above it should project to same XY, Z=0
    dst = [0.0, 0.0, 0.0]
    project_point_on_plane(dst, [3.0, 4.0, 5.0], [0.0, 0.0, 1.0])
    assert abs(dst[0] - 3.0) < EPS
    assert abs(dst[1] - 4.0) < EPS
    assert abs(dst[2]) < EPS


def test_project_point_on_plane_already_on_plane():
    dst = [0.0, 0.0, 0.0]
    # Point [1,0,0] already on the YZ plane (normal=[1,0,0]) only if dot=0
    # Actually [2,3,0] projected onto Z-plane with normal[0,0,1]: Z component removed
    project_point_on_plane(dst, [2.0, 3.0, 0.0], [0.0, 0.0, 1.0])
    assert abs(dst[0] - 2.0) < EPS
    assert abs(dst[1] - 3.0) < EPS
    assert abs(dst[2]) < EPS


def test_project_point_on_plane_result_perpendicular_to_normal():
    dst = [0.0, 0.0, 0.0]
    normal = [1.0, 1.0, 0.0]
    q_shared.vec_normalize(normal)
    project_point_on_plane(dst, [5.0, 3.0, 2.0], normal)
    # dst must be perpendicular to normal (dot product = 0)
    assert abs(q_shared.dot_product(dst, normal)) < EPS


# ===== r_concat_rotations =====

def _identity3():
    return [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]


def _zero3():
    return [[0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]]


def test_r_concat_rotations_identity():
    identity = _identity3()
    out = _zero3()
    r_concat_rotations(identity, identity, out)
    for i in range(3):
        for j in range(3):
            assert abs(out[i][j] - identity[i][j]) < EPS


def test_r_concat_rotations_with_matrix():
    a = [[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0],
         [7.0, 8.0, 9.0]]
    identity = _identity3()
    out = _zero3()
    r_concat_rotations(a, identity, out)
    for i in range(3):
        for j in range(3):
            assert abs(out[i][j] - a[i][j]) < EPS


def test_r_concat_rotations_simple():
    # 90-degree rotation around Z:
    # [[0,-1,0],[1,0,0],[0,0,1]]
    # Applied twice should give 180-degree rotation: [[-1,0,0],[0,-1,0],[0,0,1]]
    rot90 = [[0.0, -1.0, 0.0],
             [1.0,  0.0, 0.0],
             [0.0,  0.0, 1.0]]
    out = _zero3()
    r_concat_rotations(rot90, rot90, out)
    expected = [[-1.0, 0.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0,  0.0, 1.0]]
    for i in range(3):
        for j in range(3):
            assert abs(out[i][j] - expected[i][j]) < EPS


# ===== r_concat_transforms =====

def _identity4():
    return [[1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0]]


def _zero4():
    return [[0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0]]


def test_r_concat_transforms_identity():
    identity = _identity4()
    out = _zero4()
    r_concat_transforms(identity, identity, out)
    for i in range(3):
        for j in range(4):
            assert abs(out[i][j] - identity[i][j]) < EPS


def test_r_concat_transforms_translation_compose():
    # Two translations should add up
    t1 = [[1.0, 0.0, 0.0, 5.0],
          [0.0, 1.0, 0.0, 3.0],
          [0.0, 0.0, 1.0, 1.0]]
    t2 = [[1.0, 0.0, 0.0, 2.0],
          [0.0, 1.0, 0.0, 4.0],
          [0.0, 0.0, 1.0, 6.0]]
    out = _zero4()
    r_concat_transforms(t1, t2, out)
    # Rotation part should still be identity
    for i in range(3):
        for j in range(3):
            assert abs(out[i][j] - (1.0 if i == j else 0.0)) < EPS
    # Translation: t1 * t2 translation = t1_rot * t2_trans + t1_trans
    assert abs(out[0][3] - 7.0) < EPS
    assert abs(out[1][3] - 7.0) < EPS
    assert abs(out[2][3] - 7.0) < EPS


def test_r_concat_transforms_identity_with_translation():
    t = [[1.0, 0.0, 0.0, 10.0],
         [0.0, 1.0, 0.0, 20.0],
         [0.0, 0.0, 1.0, 30.0]]
    identity = _identity4()
    out = _zero4()
    r_concat_transforms(t, identity, out)
    for i in range(3):
        for j in range(4):
            assert abs(out[i][j] - t[i][j]) < EPS
