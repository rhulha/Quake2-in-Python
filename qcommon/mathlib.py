"""
mathlib.py - Quake 2 math library extensions
Translated from q_shared.c
"""

import math
from . import q_shared


def rotate_point_around_vector(dst, dir_vec, point, degrees):
    """RotatePointAroundVector(dst, dir, point, degrees) - rotate point around vector"""
    rad = math.radians(degrees)
    cos_angle = math.cos(rad)
    sin_angle = math.sin(rad)

    # Normalize the direction vector
    dir_norm = [0.0, 0.0, 0.0]
    q_shared.vec_copy(dir_vec, dir_norm)
    q_shared.vec_normalize(dir_norm)

    # Use Rodrigues' rotation formula
    # v_rot = v*cos(θ) + (k×v)*sin(θ) + k*(k·v)*(1-cos(θ))

    # k · v
    k_dot_v = q_shared.dot_product(dir_norm, point)

    # k × v
    cross = [0.0, 0.0, 0.0]
    q_shared.cross_product(dir_norm, point, cross)

    # v_rot = v*cos + (k×v)*sin + k*(k·v)*(1-cos)
    dst[0] = point[0] * cos_angle + cross[0] * sin_angle + dir_norm[0] * k_dot_v * (1 - cos_angle)
    dst[1] = point[1] * cos_angle + cross[1] * sin_angle + dir_norm[1] * k_dot_v * (1 - cos_angle)
    dst[2] = point[2] * cos_angle + cross[2] * sin_angle + dir_norm[2] * k_dot_v * (1 - cos_angle)


def perpendicular_vector(dst, src):
    """PerpendicularVector(dst, src) - compute perpendicular vector to src"""
    abs_x = abs(src[0])
    abs_y = abs(src[1])
    abs_z = abs(src[2])

    if abs_x <= abs_y and abs_x <= abs_z:
        dst[0] = 0.0
        dst[1] = -src[2]
        dst[2] = src[1]
    elif abs_y <= abs_x and abs_y <= abs_z:
        dst[0] = -src[2]
        dst[1] = 0.0
        dst[2] = src[0]
    else:
        dst[0] = -src[1]
        dst[1] = src[0]
        dst[2] = 0.0

    q_shared.vec_normalize(dst)


def project_point_on_plane(dst, p, normal):
    """ProjectPointOnPlane(dst, p, normal) - project point onto plane"""
    d = q_shared.dot_product(normal, p)
    dst[0] = p[0] - d * normal[0]
    dst[1] = p[1] - d * normal[1]
    dst[2] = p[2] - d * normal[2]


def r_concat_rotations(in1, in2, out):
    """R_ConcatRotations(in1[3][3], in2[3][3], out[3][3]) - matrix multiplication"""
    # Matrix format: row-major 3x3
    for i in range(3):
        for j in range(3):
            out[i][j] = (in1[i][0] * in2[0][j] +
                        in1[i][1] * in2[1][j] +
                        in1[i][2] * in2[2][j])


def r_concat_transforms(in1, in2, out):
    """R_ConcatTransforms(in1[3][4], in2[3][4], out[3][4]) - transform concatenation"""
    # Transform format: 3x4 matrix [rotation|translation]
    for i in range(3):
        for j in range(3):
            out[i][j] = (in1[i][0] * in2[0][j] +
                        in1[i][1] * in2[1][j] +
                        in1[i][2] * in2[2][j])

        out[i][3] = (in1[i][0] * in2[0][3] +
                    in1[i][1] * in2[1][3] +
                    in1[i][2] * in2[2][3] +
                    in1[i][3])
