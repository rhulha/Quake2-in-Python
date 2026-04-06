"""
Unit tests for qcommon/__init__.py package exports.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qcommon


def test_qcommon_exports_modules_in_all():
    assert hasattr(qcommon, '__all__')
    assert 'q_shared' in qcommon.__all__
    assert 'mathlib' in qcommon.__all__


def test_qcommon_q_shared_module_accessible():
    assert hasattr(qcommon, 'q_shared')
    assert hasattr(qcommon.q_shared, 'dot_product')


def test_qcommon_mathlib_module_accessible():
    assert hasattr(qcommon, 'mathlib')
    assert hasattr(qcommon.mathlib, 'rotate_point_around_vector')
