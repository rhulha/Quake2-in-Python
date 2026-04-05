from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions


LinkEmptyFunctions(globals(), [])


def CL_ParseInventory():
    return


def Inv_DrawString():
    return


def SetStringHighBit(s):
    for i in range(len(s)):
        s[i] = chr(ord(s[i]) | 128)


def CL_DrawInventory():
    return

