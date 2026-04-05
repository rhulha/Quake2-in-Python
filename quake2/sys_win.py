from wrapper_qpy.decorators import va_args, TODO
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QCrossPlatform import MessageBox
from shared.QConstants import NULL


LinkEmptyFunctions(globals(), ["Qcommon_Init"])

ActiveApp = 0


@va_args
def Sys_Error(error):
    MessageBox(NULL, text, "Error", 0)
    # TODO: check qwclsemaphore & DeinitConProc()
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


@TODO
def WinMain(argc, argv):
    Qcommon_Init(argc, argv)
    # TODO: continue from here
    return 1


from .common import Qcommon_Init


