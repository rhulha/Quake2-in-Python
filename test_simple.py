"""
Simple functional tests for Quake 2 Python systems
"""

def test_file_system():
    """Test file loading"""
    print("Testing file system...")
    from quake2.files import FS_InitFilesystem, FS_LoadFile

    try:
        FS_InitFilesystem()
        print("  File system initialized")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def test_command_system():
    """Test command buffer"""
    print("Testing command system...")
    from quake2.cmd import Cbuf_Init, Cbuf_AddText, Cbuf_Execute, Cmd_AddCommand

    try:
        Cbuf_Init()
        Cmd_AddCommand("test", lambda: print("    Test command executed"))
        Cbuf_AddText("test\n")
        Cbuf_Execute()
        print("  Command system working")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def test_cvar_system():
    """Test console variables"""
    print("Testing console variables...")
    from quake2.cvar import Cvar_Get, Cvar_Set, Cvar_FindVar

    try:
        v = Cvar_Get("test_var", "100", 0)
        Cvar_Set("test_var", "200")
        v2 = Cvar_FindVar("test_var")
        if v2 and v2['string'] == "200":
            print("  Cvar system working")
            return True
        else:
            print("  Cvar value mismatch")
            return False
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def test_physics():
    """Test player physics"""
    print("Testing player physics...")
    from quake2.pmove import pmove_t, Pmove

    try:
        pm = pmove_t()
        pm.origin = [0, 0, 0]
        pm.velocity = [100, 0, 0]
        pm.viewangles = [0, 0, 0]
        pm.groundentity = True
        pm.cmd = None

        Pmove(pm)

        # Verify gravity was applied
        if pm.velocity[2] < 0:
            print("  Physics working (gravity applied)")
            return True
        else:
            print("  Physics issue: no gravity")
            return False
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def test_renderer():
    """Test renderer modules"""
    print("Testing renderer modules...")
    try:
        from ref_gl import glw_imp, gl_rmain, gl_image, gl_model
        print("  Renderer modules load successfully")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def test_game():
    """Test game module"""
    print("Testing game module...")
    try:
        from game import G_Init, G_RunFrame
        G_Init()
        G_RunFrame()
        print("  Game module working")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Quake 2 Python - Functional Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_file_system,
        test_command_system,
        test_cvar_system,
        test_physics,
        test_renderer,
        test_game,
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
            print(f"  ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\nAll systems functional! Ready for Phase 2 implementation.")
    else:
        print(f"\nSome systems need work: {failed} failures")

    return failed == 0


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
