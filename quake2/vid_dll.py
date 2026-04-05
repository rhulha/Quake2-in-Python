from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])


def WIN_DisableAltTab():
    return


def WIN_EnableAltTab():
    return


def VID_Printf(print_level, msg):
    if print_level == 0:
        print(msg, end='')


def VID_Error(print_level, msg):
    raise RuntimeError(msg)


def MapKey(key):
    return key


def AppActivate(fActive, minimize):
    return


def MainWndProc(hWnd, uMsg, wParam, lParam):
    return 0


def VID_Restart_f():
    return


def VID_Front_f():
    return


def VID_GetModeInfo(width, height, mode):
    modes = [(320, 240), (400, 300), (512, 384), (640, 480), (800, 600),
             (1024, 768), (1280, 960), (1600, 1200)]
    if 0 <= mode < len(modes):
        if hasattr(width, 'value'):
            width.value = modes[mode][0]
        if hasattr(height, 'value'):
            height.value = modes[mode][1]
        return True
    return False


def VID_UpdateWindowPosAndSize(x, y):
    return


def VID_NewWindow(width, height):
    return


def VID_FreeReflib():
    return


def VID_LoadRefresh():
    return True


def VID_CheckChanges():
    return


def VID_Init():
    return


def VID_Shutdown():
    return
