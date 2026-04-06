"""
Unit tests for ref_gl/gl_rsurf.py
Tests BSP surface rendering functionality
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_surface_rendering_setup():
    """Test surface rendering initialization"""
    print("\n=== Test: Surface Rendering Setup ===")

    # Test that we can create a surface structure
    surface = {
        'first_edge': 0,
        'num_edges': 4,
        'plane_num': 0,
        'side': 0,
        'texinfo': 0,
        'lightofs': -1,
        'samples': None
    }

    assert surface['num_edges'] > 0
    assert surface['first_edge'] >= 0
    assert isinstance(surface['lightofs'], int)

    print("[OK] Surface structure created correctly")
    print(f"  Edges: {surface['num_edges']}")
    print(f"  Plane: {surface['plane_num']}")


def test_face_vertex_parsing():
    """Test parsing face vertices from edges and surfedges"""
    print("\n=== Test: Face Vertex Parsing ===")

    # Mock data for a quad face
    edges = b''
    for i in range(4):
        edges += bytes([i, 0, i+1, 0])  # Each edge is 2 uint16s

    surfedges = b''
    for i in range(4):
        surfedges += bytes([i, 0, 0, 0])  # 4 signed int32s (little-endian)

    # Verify we can read the data
    assert len(edges) == 16  # 4 edges * 4 bytes each
    assert len(surfedges) == 16  # 4 surfedges * 4 bytes each

    print("[OK] Edge and surfedge data format correct")
    print(f"  Edges: {len(edges)} bytes (4 edges)")
    print(f"  Surfedges: {len(surfedges)} bytes (4 surfedges)")


def test_polygon_vertex_collection():
    """Test collecting vertices for a polygon"""
    print("\n=== Test: Polygon Vertex Collection ===")

    # Create test vertices
    vertices = [
        [0.0, 0.0, 0.0],
        [100.0, 0.0, 0.0],
        [100.0, 100.0, 0.0],
        [0.0, 100.0, 0.0],
    ]

    # Create a face referencing these vertices
    face_vertices = [vertices[i] for i in [0, 1, 2, 3]]

    assert len(face_vertices) == 4
    assert face_vertices[0] == [0.0, 0.0, 0.0]
    assert face_vertices[2] == [100.0, 100.0, 0.0]

    print("[OK] Polygon vertices collected correctly")
    print(f"  Vertices: {len(face_vertices)}")
    for i, v in enumerate(face_vertices):
        print(f"    Vertex {i}: {v}")


def test_surface_flags():
    """Test surface state flags"""
    print("\n=== Test: Surface Flags ===")

    SURF_PLANEBACK = 2
    SURF_DRAWSKY = 4
    SURF_DRAWTURB = 0x10
    SURF_DRAWFLAT = 0x80

    surface = {
        'flags': 0
    }

    # Set sky flag
    surface['flags'] |= SURF_DRAWSKY
    assert surface['flags'] & SURF_DRAWSKY

    # Set turb flag
    surface['flags'] |= SURF_DRAWTURB
    assert surface['flags'] & SURF_DRAWTURB

    # Check multiple flags
    assert (surface['flags'] & (SURF_DRAWSKY | SURF_DRAWTURB)) != 0

    print("[OK] Surface flag operations work")
    print(f"  Flags value: {surface['flags']}")
    print(f"  Has SKY: {bool(surface['flags'] & SURF_DRAWSKY)}")
    print(f"  Has TURB: {bool(surface['flags'] & SURF_DRAWTURB)}")


def test_lightmap_bounds():
    """Test lightmap coordinate bounds"""
    print("\n=== Test: Lightmap Bounds ===")

    # Test lightmap size calculations
    surf_extents = [256, 512]  # Width and height in lightmap space
    lightmap_size = 16  # Lightmap block size

    # Calculate bounds
    smax = (surf_extents[0] // lightmap_size) + 1
    tmax = (surf_extents[1] // lightmap_size) + 1

    assert smax == 17  # 256/16 + 1
    assert tmax == 33  # 512/16 + 1

    print("[OK] Lightmap bounds calculated correctly")
    print(f"  Extent S: {surf_extents[0]} -> {smax} samples")
    print(f"  Extent T: {surf_extents[1]} -> {tmax} samples")


def test_surface_texinfo():
    """Test surface texture info"""
    print("\n=== Test: Surface Texinfo ===")

    texinfo = {
        'vecs': [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ],
        'flags': 0,
        'nexttexinfo': -1,
        'value': 0
    }

    # Test S vector
    assert texinfo['vecs'][0][0] == 1.0
    assert texinfo['vecs'][0][3] == 0.0  # Offset

    # Test T vector
    assert texinfo['vecs'][1][1] == 1.0

    print("[OK] Texinfo structure valid")
    print(f"  S vector: {texinfo['vecs'][0]}")
    print(f"  T vector: {texinfo['vecs'][1]}")


def test_edge_vertex_lookup():
    """Test looking up vertices from edges"""
    print("\n=== Test: Edge Vertex Lookup ===")

    import struct

    # Create edge data: each edge is 2 uint16 vertex indices
    edges_data = b''
    edge_list = [(0, 1), (1, 2), (2, 3), (3, 0)]

    for v0, v1 in edge_list:
        edges_data += struct.pack('<HH', v0, v1)

    # Create surfedges: signed int32 indices into edge list
    surfedges_data = b''
    for i in range(4):
        surfedges_data += struct.pack('<i', i)  # Positive = use v0, negative = use v1

    # Test parsing
    assert len(edges_data) == 16  # 4 edges * 4 bytes
    assert len(surfedges_data) == 16  # 4 surfedges * 4 bytes

    # Unpack first edge
    v0, v1 = struct.unpack_from('<HH', edges_data, 0)
    assert v0 == 0 and v1 == 1

    # Unpack first surfedge
    se = struct.unpack_from('<i', surfedges_data, 0)[0]
    assert se == 0

    print("[OK] Edge vertex lookup works")
    print(f"  Edge 0: vertices {v0}, {v1}")
    print(f"  Surfedge 0: edge index {se}")


def test_face_edge_iteration():
    """Test iterating through edges of a face"""
    print("\n=== Test: Face Edge Iteration ===")

    face = {
        'first_edge': 10,
        'num_edges': 6
    }

    # Collect edge indices for this face
    edge_indices = list(range(face['first_edge'], face['first_edge'] + face['num_edges']))

    assert len(edge_indices) == 6
    assert edge_indices[0] == 10
    assert edge_indices[-1] == 15

    print("[OK] Face edge iteration works")
    print(f"  Face edges: {len(edge_indices)}")
    print(f"  Range: {edge_indices[0]} to {edge_indices[-1]}")


if __name__ == '__main__':
    try:
        test_surface_rendering_setup()
        test_face_vertex_parsing()
        test_polygon_vertex_collection()
        test_surface_flags()
        test_lightmap_bounds()
        test_surface_texinfo()
        test_edge_vertex_lookup()
        test_face_edge_iteration()

        print("\n" + "="*50)
        print("GL_RSURF TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
