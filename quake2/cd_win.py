from wrapper_qpy.linker import LinkEmptyFunctions


LinkEmptyFunctions(globals(), [])


"""
    We will be skipping most of these functions as they only contain
    reading the data from the cd
"""


def CDAudio_Play2(track, looping):
    return


def CDAudio_Play(track, looping):
    return


def CDAudio_Stop():
    return


def CDAudio_Pause():
    return


def CDAudio_Resume():
    return


def CDAudio_Stop():
    return


def CDAudio_MessageHandler(hWnd, uMsg, wParam, lParam):
    return


def CDAudio_Update():
    return


def CDAudio_Init():
    return


def CDAudio_Shutdown():
    return


def CDAudio_Activate(actuve):
    return

