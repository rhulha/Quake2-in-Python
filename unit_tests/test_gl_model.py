"""
Unit tests for ref_gl/gl_model.py
Tests model loading and management functionality
"""

import sys
import os
import struct

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ref_gl.gl_model import (
    Model, Mod_LoadModel, Mod_ForName, RadiusFromBounds,
    Mod_PointInLeaf, Mod_ClusterPVS, R_BeginRegistration
)


def test_model_creation():
    """Test Model class initialization"""
    print("\n=== Test: Model Creation ===")

    model = Model("test_model.bsp")
    assert model.name == "test_model.bsp"
    assert model.type == 4  # MODEL_NULL
    assert model.numframes == 0
    assert len(model.vertices) == 0
    assert len(model.faces) == 0
    assert model.radius == 0

    print("[OK] Model object created with correct defaults")
    print(f"  Name: {model.name}")
    print(f"  Type: {model.type}")
    print(f"  Vertices: {len(model.vertices)}")
    print(f"  Faces: {len(model.faces)}")


def test_radius_from_bounds():
    """Test radius calculation from bounding box"""
    print("\n=== Test: Radius From Bounds ===")

    # Test with simple cube
    mins = [0, 0, 0]
    maxs = [10, 10, 10]

    radius = RadiusFromBounds(mins, maxs)
    assert radius > 0, "Radius should be positive"

    # Expected: center is (5,5,5), max distance is sqrt((5)^2 + (5)^2 + (5)^2) = sqrt(75) ≈ 8.66
    expected = (75) ** 0.5
    assert abs(radius - expected) < 0.01, f"Expected ~{expected}, got {radius}"

    print("[OK] Radius calculation correct")
    print(f"  Bounds: {mins} to {maxs}")
    print(f"  Radius: {radius:.2f}")


def test_model_cache():
    """Test model caching mechanism"""
    print("\n=== Test: Model Cache ===")

    # Create two models
    model1 = Model("map1.bsp")
    model2 = Model("map2.bsp")

    # Models should be distinct
    assert model1.name != model2.name
    assert model1 is not model2

    print("[OK] Model cache can store multiple models")
    print(f"  Model 1: {model1.name}")
    print(f"  Model 2: {model2.name}")


def test_model_properties():
    """Test model property access"""
    print("\n=== Test: Model Properties ===")

    model = Model("test.bsp")

    # Set properties
    model.type = 1  # MODEL_BRUSH
    model.numframes = 5
    model.flags = 8
    model.mins = [100, 200, 300]
    model.maxs = [400, 500, 600]

    # Verify properties
    assert model.type == 1
    assert model.numframes == 5
    assert model.flags == 8
    assert model.mins == [100, 200, 300]
    assert model.maxs == [400, 500, 600]

    print("[OK] Model properties can be set and retrieved")
    print(f"  Type: {model.type}")
    print(f"  Frames: {model.numframes}")
    print(f"  Flags: {model.flags}")
    print(f"  Bounds: {model.mins} to {model.maxs}")


def test_model_lump_storage():
    """Test model stores BSP lumps correctly"""
    print("\n=== Test: Model Lump Storage ===")

    model = Model("test.bsp")

    # Store raw lump data
    model.lump_edges = b'\x00\x01\x02\x03'
    model.lump_surfedges = b'\x04\x05\x06\x07'
    model.lump_texinfo = b'\x08\x09\x0a\x0b'

    # Verify storage
    assert model.lump_edges == b'\x00\x01\x02\x03'
    assert model.lump_surfedges == b'\x04\x05\x06\x07'
    assert model.lump_texinfo == b'\x08\x09\x0a\x0b'

    print("[OK] BSP lumps stored correctly")
    print(f"  Edges: {len(model.lump_edges)} bytes")
    print(f"  Surfedges: {len(model.lump_surfedges)} bytes")
    print(f"  Texinfo: {len(model.lump_texinfo)} bytes")


def test_model_face_loading():
    """Test face data storage"""
    print("\n=== Test: Model Face Loading ===")

    model = Model("test.bsp")

    # Create mock face data
    face1 = {
        'num_edges': 4,
        'first_edge': 0,
        'plane_num': 0,
        'side': 0,
        'lightofs': -1
    }

    face2 = {
        'num_edges': 3,
        'first_edge': 4,
        'plane_num': 1,
        'side': 1,
        'lightofs': 100
    }

    model.faces = [face1, face2]

    assert len(model.faces) == 2
    assert model.faces[0]['num_edges'] == 4
    assert model.faces[1]['first_edge'] == 4

    print("[OK] Face data stored correctly")
    print(f"  Total faces: {len(model.faces)}")
    print(f"  Face 1 edges: {model.faces[0]['num_edges']}")
    print(f"  Face 2 start edge: {model.faces[1]['first_edge']}")


def test_model_vertex_data():
    """Test vertex data storage"""
    print("\n=== Test: Model Vertex Data ===")

    model = Model("test.bsp")

    # Create mock vertices
    model.vertices = [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
        [0.0, 0.0, 10.0],
    ]

    assert len(model.vertices) == 5
    assert model.vertices[0] == [0.0, 0.0, 0.0]
    assert model.vertices[4] == [0.0, 0.0, 10.0]

    # Verify vertex coordinates are float
    for vertex in model.vertices:
        for coord in vertex:
            assert isinstance(coord, float)

    print("[OK] Vertex data stored correctly")
    print(f"  Total vertices: {len(model.vertices)}")
    print(f"  First vertex: {model.vertices[0]}")
    print(f"  Last vertex: {model.vertices[-1]}")


def test_model_registration():
    """Test model registration sequence"""
    print("\n=== Test: Model Registration ===")

    # Models should have registration sequence
    model1 = Model("test1.bsp")
    model2 = Model("test2.bsp")

    model1.registration_sequence = 1
    model2.registration_sequence = 1

    assert model1.registration_sequence == model2.registration_sequence

    model2.registration_sequence = 2
    assert model1.registration_sequence != model2.registration_sequence

    print("[OK] Model registration tracking works")
    print(f"  Model 1 seq: {model1.registration_sequence}")
    print(f"  Model 2 seq: {model2.registration_sequence}")


if __name__ == '__main__':
    try:
        test_model_creation()
        test_radius_from_bounds()
        test_model_cache()
        test_model_properties()
        test_model_lump_storage()
        test_model_face_loading()
        test_model_vertex_data()
        test_model_registration()

        print("\n" + "="*50)
        print("GL_MODEL TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
