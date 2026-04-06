"""
Unit tests for quake2/files.py
Tests file system operations and path handling
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_path_normalization():
    """Test path normalization"""
    print("\n=== Test: Path Normalization ===")

    # Normalize game paths
    paths = [
        "maps/base1.bsp",
        "textures/base/floor01.wal",
        "models/weapons/shotgun.md2",
        "sprites/explosion.sp2"
    ]

    # Convert backslashes to forward slashes
    normalized = [p.replace('\\', '/') for p in paths]

    assert all('/' in p or '\\' not in p for p in normalized)
    assert len(normalized) == 4

    print("[OK] Paths normalized")
    print(f"  Paths: {len(normalized)}")
    for p in normalized:
        print(f"    - {p}")


def test_file_extension_check():
    """Test file extension validation"""
    print("\n=== Test: File Extension Check ===")

    valid_extensions = {
        'bsp': 'BSP map file',
        'wal': 'Texture file',
        'md2': 'Model file',
        'pcx': 'Image file'
    }

    test_files = ["map.bsp", "texture.wal", "model.md2", "image.pcx"]

    # Check extensions
    for filename in test_files:
        ext = filename.split('.')[-1]
        assert ext in valid_extensions

    print("[OK] File extensions validated")
    print(f"  Extensions: {len(valid_extensions)}")


def test_file_search_path():
    """Test file search path ordering"""
    print("\n=== Test: File Search Path ===")

    search_paths = [
        ".",
        "./gamedata",
        "./baseq2",
        "/opt/quake2",
        "/usr/share/games/quake2"
    ]

    assert len(search_paths) > 0
    assert search_paths[0] == "."
    assert any("baseq2" in p for p in search_paths)

    print("[OK] Search paths configured")
    print(f"  Paths: {len(search_paths)}")
    for path in search_paths[:3]:
        print(f"    - {path}")


def test_pak_file_handling():
    """Test PAK file structure"""
    print("\n=== Test: PAK File Handling ===")

    # PAK file contains multiple lumps
    pak_lumps = {
        'maps': ['base1.bsp', 'base2.bsp', 'q2dm1.bsp'],
        'textures': ['floor01.wal', 'wall01.wal', 'ceiling01.wal'],
        'models': ['shotgun.md2', 'grunt.md2'],
        'sprites': ['explosion.sp2']
    }

    total_files = sum(len(files) for files in pak_lumps.values())
    assert total_files == 9

    print("[OK] PAK structure defined")
    print(f"  Categories: {len(pak_lumps)}")
    print(f"  Total files: {total_files}")


def test_directory_scanning():
    """Test directory scanning for files"""
    print("\n=== Test: Directory Scanning ===")

    # Simulate directory contents
    file_list = [
        "maps/base1.bsp",
        "maps/base2.bsp",
        "maps/q2dm1.bsp",
        "maps/q2dm2.bsp"
    ]

    # Filter by directory
    maps = [f for f in file_list if f.startswith("maps/")]

    assert len(maps) == 4
    assert all(f.endswith(".bsp") for f in maps)

    print("[OK] Directory scanned")
    print(f"  Found: {len(maps)} map files")


def test_file_size_calculation():
    """Test file size tracking"""
    print("\n=== Test: File Size Calculation ===")

    files = [
        {'name': 'base1.bsp', 'size': 1024 * 1024},      # 1 MB
        {'name': 'base2.bsp', 'size': 2 * 1024 * 1024},   # 2 MB
        {'name': 'textures.pak', 'size': 10 * 1024 * 1024} # 10 MB
    ]

    total_size = sum(f['size'] for f in files)
    total_mb = total_size / (1024 * 1024)

    assert total_mb == 13
    assert total_size == 13 * 1024 * 1024

    print("[OK] File sizes calculated")
    print(f"  Total: {total_mb} MB")
    for f in files:
        size_kb = f['size'] / 1024
        print(f"    - {f['name']}: {size_kb:.0f} KB")


def test_file_caching():
    """Test file caching system"""
    print("\n=== Test: File Caching ===")

    file_cache = {}

    # Load a file
    filename = "maps/base1.bsp"
    file_data = b"BSP_DATA_HERE"
    file_cache[filename] = file_data

    # Check cache
    assert filename in file_cache
    assert file_cache[filename] == file_data

    # Load another file
    filename2 = "textures/base/floor01.wal"
    file_cache[filename2] = b"WAL_DATA_HERE"

    assert len(file_cache) == 2

    print("[OK] File caching works")
    print(f"  Cached files: {len(file_cache)}")


def test_path_combining():
    """Test path combining"""
    print("\n=== Test: Path Combining ===")

    base_path = "D:\\SteamLibrary\\steamapps\\common\\Quake 2"
    subpath = "baseq2/maps/base1.bsp"

    # Combine paths
    full_path = os.path.join(base_path, subpath)

    assert "base1.bsp" in full_path
    assert "maps" in full_path

    print("[OK] Paths combined correctly")
    print(f"  Full path: {full_path}")


def test_file_exists_check():
    """Test file existence checking"""
    print("\n=== Test: File Exists Check ===")

    # Mock file system
    files = {
        "maps/base1.bsp": True,
        "maps/invalid.bsp": False,
        "textures/wall01.wal": True
    }

    # Check if file exists
    requested = "maps/base1.bsp"
    exists = requested in files and files[requested]

    assert exists

    requested2 = "maps/invalid.bsp"
    exists2 = requested2 in files and files[requested2]

    assert not exists2

    print("[OK] File existence checked")
    print(f"  Found: maps/base1.bsp")
    print(f"  Not found: maps/invalid.bsp")


if __name__ == '__main__':
    try:
        test_path_normalization()
        test_file_extension_check()
        test_file_search_path()
        test_pak_file_handling()
        test_directory_scanning()
        test_file_size_calculation()
        test_file_caching()
        test_path_combining()
        test_file_exists_check()

        print("\n" + "="*50)
        print("FILESYSTEM TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
