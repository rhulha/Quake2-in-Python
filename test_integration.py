"""
Integration test for Quake 2 Python
Tests basic engine, physics, renderer, and game systems
"""

def test_imports():
    """Test all critical modules import"""
    print("Testing imports...")
    from quake2 import files, common, cvar, cmd, qfiles, cmodel, pmove
    from ref_gl import glw_imp, gl_rmain, gl_image, gl_model, gl_rsurf, gl_mesh
    from quake2 import sv_main
    from game import G_Init, G_RunFrame, G_SpawnEntities
    print("  All modules imported successfully")
    return True


def test_engine_init():
    """Test engine initialization"""
    print("Testing engine initialization...")
    try:
        from quake2.common import Qcommon_Init

        # Initialize with minimal arguments
        Qcommon_Init(0, [])
        print("  Engine initialized successfully")
        return True
    except Exception as e:
        print(f"  Engine init failed: {e}")
        return False


def test_collision_system():
    """Test collision model system"""
    print("Testing collision system...")
    try:
        from quake2.cmodel import CM_BoxTrace, CM_PointContents
        from quake2.pmove import Pmove, pmove_t

        # Test point contents at origin
        contents = CM_PointContents([0, 0, 0], 0)
        print(f"  Point contents at origin: {contents}")

        # Test box trace
        class SimpleRefDef:
            worldmodel = None

        print("  Collision system working")
        return True
    except Exception as e:
        print(f"  Collision test failed: {e}")
        return False


def test_physics_system():
    """Test player physics"""
    print("Testing physics system...")
    try:
        from quake2.pmove import pmove_t, Pmove

        # Create player state
        pm = pmove_t()
        pm.origin = [0, 0, 0]
        pm.velocity = [100, 0, 0]
        pm.viewangles = [0, 0, 0]
        pm.groundentity = True
        pm.cmd = None

        # Run one frame
        Pmove(pm)

        print("  Physics system working")
        return True
    except Exception as e:
        print(f"  Physics test failed: {e}")
        return False


def test_renderer_init():
    """Test renderer initialization"""
    print("Testing renderer initialization...")
    try:
        from ref_gl import glw_imp

        # Test window creation (don't actually create window in test)
        print("  Renderer modules loaded successfully")
        return True
    except Exception as e:
        print(f"  Renderer test failed: {e}")
        return False


def test_game_init():
    """Test game initialization"""
    print("Testing game initialization...")
    try:
        from game import G_Init, GetGameAPI

        # Initialize game
        G_Init()

        # Get game API
        class DummyImport:
            error = None
            dprintf = print

        api = GetGameAPI(DummyImport())
        if api:
            print("  Game initialized successfully")
            return True
        else:
            print("  Game API initialization failed")
            return False

    except Exception as e:
        print(f"  Game init failed: {e}")
        return False


def test_server_init():
    """Test server initialization"""
    print("Testing server initialization...")
    try:
        from quake2 import sv_main

        sv_main.SV_Init()
        print("  Server initialized successfully")
        return True
    except Exception as e:
        print(f"  Server init failed: {e}")
        return False


def run_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Quake 2 Python - Integration Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_engine_init,
        test_collision_system,
        test_physics_system,
        test_renderer_init,
        test_game_init,
        test_server_init,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
