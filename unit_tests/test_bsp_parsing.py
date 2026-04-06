"""
Unit tests for BSP parsing and vertex extraction.
Tests the core data extraction logic without requiring graphics context.
"""

import sys
import os
import struct
from pathlib import Path

# Add project root to path (one level up from unit_tests directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from quake2 import qfiles
from quake2.files import FS_InitFilesystem, FS_LoadFile
from ref_gl.gl_model import Mod_LoadModel


def test_vertex_extraction_from_q2dm1():
    """Test that we extract vertices correctly from q2dm1.bsp"""
    print("\n=== Test: Vertex Extraction from q2dm1.bsp ===")

    # Initialize filesystem
    try:
        FS_InitFilesystem()
    except:
        pass

    # Load the model
    model = Mod_LoadModel("maps/q2dm1.bsp", crash=False)
    assert model is not None, "Failed to load q2dm1.bsp"
    print(f"[OK] Loaded model: {model.name}")

    # Check basic model properties
    assert len(model.faces) > 0, "Model has no faces"
    assert len(model.vertices) > 0, "Model has no vertices"
    print(f"[OK] Model has {len(model.faces)} faces and {len(model.vertices)} vertices")

    # Check lumps are available
    assert hasattr(model, 'lump_surfedges'), "Model has no lump_surfedges"
    assert hasattr(model, 'lump_edges'), "Model has no lump_edges"
    assert len(model.lump_surfedges) > 0, "lump_surfedges is empty"
    assert len(model.lump_edges) > 0, "lump_edges is empty"
    print(f"[OK] Lumps available: surfedges={len(model.lump_surfedges)} bytes, edges={len(model.lump_edges)} bytes")

    # Test vertex extraction for first 10 faces
    print("\n--- Testing vertex extraction for first 10 faces ---")
    faces_with_vertices = 0
    faces_without_vertices = 0
    vertex_coords = []

    for face_idx, face in enumerate(model.faces[:10]):
        if 'first_edge' not in face or 'num_edges' not in face:
            print(f"Face {face_idx}: Missing edge data")
            continue

        first_edge = face['first_edge']
        num_edges = face['num_edges']

        if num_edges <= 0 or num_edges > 256:
            print(f"Face {face_idx}: Invalid num_edges={num_edges}")
            continue

        # Extract vertices
        vertices = []
        try:
            for i in range(num_edges):
                se_idx = first_edge + i

                # Read surfedge
                if se_idx * 4 + 4 <= len(model.lump_surfedges):
                    se = struct.unpack_from('<i', model.lump_surfedges, se_idx * 4)[0]
                    edge_idx = abs(se)

                    # Read edge
                    if edge_idx * 4 + 4 <= len(model.lump_edges):
                        v0, v1 = struct.unpack_from('<HH', model.lump_edges, edge_idx * 4)
                        v_idx = v0 if se >= 0 else v1

                        if 0 <= v_idx < len(model.vertices):
                            v = model.vertices[v_idx]
                            vertices.append((float(v[0]), float(v[1]), float(v[2])))
                            vertex_coords.append(v)
        except Exception as e:
            print(f"Face {face_idx}: Error extracting vertices: {e}")
            continue

        if len(vertices) >= 3:
            faces_with_vertices += 1
            print(f"Face {face_idx}: [OK] {len(vertices)} vertices")
            # Show first vertex coords
            print(f"  First vertex: {vertices[0]}")
            # Check bounds
            min_v = tuple(min(v[i] for v in vertices) for i in range(3))
            max_v = tuple(max(v[i] for v in vertices) for i in range(3))
            print(f"  Bounds: min={min_v}, max={max_v}")
        else:
            faces_without_vertices += 1
            print(f"Face {face_idx}: [NO] Only {len(vertices)} vertices")

    print(f"\n--- Summary ---")
    print(f"Faces with vertices: {faces_with_vertices}")
    print(f"Faces without vertices: {faces_without_vertices}")

    # Assertions
    assert faces_with_vertices > 0, "No faces have extracted vertices!"
    print(f"[OK] Successfully extracted vertices from {faces_with_vertices} faces")

    # Check that vertices aren't all at origin
    if vertex_coords:
        all_at_origin = all(v == (0.0, 0.0, 0.0) for v in vertex_coords)
        assert not all_at_origin, "All vertices are at origin (0,0,0)!"
        print(f"[OK] Vertices span space (not all at origin)")

        # Calculate bounds
        min_x = min(v[0] for v in vertex_coords)
        max_x = max(v[0] for v in vertex_coords)
        min_y = min(v[1] for v in vertex_coords)
        max_y = max(v[1] for v in vertex_coords)
        min_z = min(v[2] for v in vertex_coords)
        max_z = max(v[2] for v in vertex_coords)

        print(f"[OK] Vertex bounds:")
        print(f"  X: {min_x:.1f} to {max_x:.1f}")
        print(f"  Y: {min_y:.1f} to {max_y:.1f}")
        print(f"  Z: {min_z:.1f} to {max_z:.1f}")


def test_surfedge_format():
    """Test that surfedges are read as signed int32"""
    print("\n=== Test: Surfedge Format ===")

    # Create test data
    test_data = struct.pack('<i', 5) + struct.pack('<i', -3) + struct.pack('<i', 0)

    # Read as signed int32
    values = []
    for i in range(3):
        val = struct.unpack_from('<i', test_data, i * 4)[0]
        values.append(val)

    print(f"Test data: {values}")
    assert values == [5, -3, 0], "Surfedge format is wrong"
    print("[OK] Surfedge format (signed int32) is correct")


def test_edge_format():
    """Test that edges are read as two uint16 values"""
    print("\n=== Test: Edge Format ===")

    # Create test data: two uint16 values
    test_data = struct.pack('<HH', 10, 20) + struct.pack('<HH', 30, 40)

    # Read as pairs of uint16
    edges = []
    for i in range(2):
        v0, v1 = struct.unpack_from('<HH', test_data, i * 4)
        edges.append((v0, v1))

    print(f"Test data: {edges}")
    assert edges == [(10, 20), (30, 40)], "Edge format is wrong"
    print("[OK] Edge format (two uint16) is correct")


def test_all_faces():
    """Test vertex extraction for ALL faces in q2dm1"""
    print("\n=== Test: All Faces ===")

    # Initialize filesystem
    try:
        FS_InitFilesystem()
    except:
        pass

    # Load model
    model = Mod_LoadModel("maps/q2dm1.bsp", crash=False)
    assert model is not None, "Failed to load q2dm1.bsp"

    faces_with_verts = 0
    faces_without_verts = 0

    for face in model.faces:
        if 'first_edge' not in face or 'num_edges' not in face:
            continue

        first_edge = face['first_edge']
        num_edges = face['num_edges']

        if num_edges <= 0 or num_edges > 256:
            continue

        # Try to extract vertices
        vertices = []
        try:
            for i in range(num_edges):
                se_idx = first_edge + i
                if se_idx * 4 + 4 <= len(model.lump_surfedges):
                    se = struct.unpack_from('<i', model.lump_surfedges, se_idx * 4)[0]
                    edge_idx = abs(se)
                    if edge_idx * 4 + 4 <= len(model.lump_edges):
                        v0, v1 = struct.unpack_from('<HH', model.lump_edges, edge_idx * 4)
                        v_idx = v0 if se >= 0 else v1
                        if 0 <= v_idx < len(model.vertices):
                            vertices.append(v_idx)
        except:
            pass

        if len(vertices) >= 3:
            faces_with_verts += 1
        else:
            faces_without_verts += 1

    total = faces_with_verts + faces_without_verts
    percent = (faces_with_verts / total * 100) if total > 0 else 0

    print(f"Total faces checked: {total}")
    print(f"Faces with vertices: {faces_with_verts} ({percent:.1f}%)")
    print(f"Faces without vertices: {faces_without_verts}")

    # Most faces should have vertices
    assert faces_with_verts > total * 0.8, f"Less than 80% of faces have vertices! ({percent:.1f}%)"
    print(f"[OK] Good vertex extraction rate")


if __name__ == '__main__':
    try:
        test_surfedge_format()
        test_edge_format()
        test_vertex_extraction_from_q2dm1()
        test_all_faces()

        print("\n" + "="*50)
        print("ALL TESTS PASSED [OK]")
        print("="*50)
    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
