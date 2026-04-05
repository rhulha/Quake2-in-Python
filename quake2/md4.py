from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions


LinkEmptyFunctions(globals(), [])


def MD4Init(context):
    return


def MD4Update(context, _input, inputLen):
    return

def MD4Final(digest, context):
    return


def MD4Transform(state, block):
    return


def Encode(output, _input, _len):
    return


def Decode(output, _input, _len):
    return


def Com_BlockChecksum(buffer, length):
    return
