from wrapper_qpy.decorators import va_args, TODO
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QCrossPlatform import MessageBox
from shared.QConstants import NULL


LinkEmptyFunctions(globals(), ["Qcommon_Init"])

ActiveApp = 0


@va_args
def Sys_Error(error):
    print(f"FATAL ERROR: {error}")
    try:
        MessageBox(NULL, error, "Error", 0)
    except:
        pass
    exit(1)

def Sys_Quit():
    return


def WinError():
    return


def Sys_ScanForCD():
    return


def Sys_CopyProtect():
    return


def Sys_Init():
    return


def Sys_ConsoleInput():
    return


def Sys_ConsoleOutput(string):
    return


def Sys_SendKeyEvents():
    return


def Sys_GetClipboardData():
    return


def Sys_AppActivate():
    return


def Sys_UnloadGame():
    return


def Sys_GetGameAPI():
    return


def ParseCommandLine():
    return


def WinMain(argc, argv):
    """Main entry point for the game"""
    try:
        import time
        from .common import Qcommon_Init, Qcommon_Frame, Qcommon_Shutdown
        from .cl_input import IN_Frame
        from ref_gl.glw_imp import GLimp_BeginFrame, GLimp_EndFrame

        # Initialize engine
        print("Initializing Quake 2 engine...")
        Qcommon_Init(argc, argv)

        print("Engine initialized. Starting main loop...")

        # Main game loop
        last_time = time.time()
        frame_count = 0

        try:
            while True:
                # Calculate frame time
                current_time = time.time()
                msec = int((current_time - last_time) * 1000.0)
                last_time = current_time

                # Cap minimum frame time
                if msec < 1:
                    msec = 1
                if msec > 200:  # Cap at 200ms (5 FPS minimum)
                    msec = 200

                # Process input first (updates key states for this frame)
                try:
                    should_continue = IN_Frame()
                    if not should_continue:
                        print("Input system signaled shutdown")
                        break
                except Exception as e:
                    print(f"IN_Frame error: {e}")

                # Run main frame (will use the input we just processed)
                try:
                    Qcommon_Frame(msec)
                except Exception as e:
                    print(f"Qcommon_Frame error: {e}")
                    import traceback
                    traceback.print_exc()
                    break

                frame_count += 1

                # Print progress every 60 frames
                if frame_count % 60 == 0:
                    fps = 1.0 / max(0.001, msec / 1000.0)
                    print(f"Frame {frame_count}: {fps:.1f} FPS")

        except KeyboardInterrupt:
            print("\nShutdown requested via keyboard")
        except Exception as e:
            print(f"Game loop error: {e}")
            import traceback
            traceback.print_exc()

        # Shutdown
        print("Shutting down...")
        try:
            Qcommon_Shutdown()
        except:
            pass

        print("Game closed normally")
        return 0

    except Exception as e:
        print(f"WinMain fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


from .common import Qcommon_Init


