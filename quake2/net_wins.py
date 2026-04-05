import socket
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

_loop_back = [{'send': [], 'get': []}] * 2
NA_LOOPBACK = 0
NA_IP = 1
NA_IPX = 2


def NetadrToSockadr(a, s):
    return


def SockadrToNetadr(s, a):
    return


def NET_CompareAdr(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.get('ip') == b.get('ip') and a.get('port') == b.get('port')
    return a == b


def NET_CompareBaseAdr(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.get('ip') == b.get('ip')
    return a == b


def NET_AdrToString(a):
    if isinstance(a, dict):
        ip = a.get('ip', [0, 0, 0, 0])
        port = a.get('port', 0)
        return '%d.%d.%d.%d:%d' % (ip[0], ip[1], ip[2], ip[3], port)
    return str(a)


def NET_StringToSockaddr(s, sadr):
    return False


def NET_StringToAdr(s, a):
    try:
        if ':' in s:
            host, port = s.rsplit(':', 1)
            a['port'] = int(port)
        else:
            host = s
            a['port'] = 27910
        ip = socket.gethostbyname(host)
        parts = [int(x) for x in ip.split('.')]
        a['ip'] = parts
        a['type'] = NA_IP
        return True
    except Exception:
        return False


def NET_IsLocalAddress(adr):
    if isinstance(adr, dict):
        return adr.get('type') == NA_LOOPBACK
    return False


def NET_GetLoopPacket(sock, net_from, net_message):
    return False


def NET_SendLoopPacket(sock, length, data, _to):
    return


def NET_GetPacket(sock, net_from, net_message):
    return False


def NET_SendPacket(sock, length, data, _to):
    return


def NET_IPSocket(net_interface, port):
    return None


def NET_OpenIP():
    return


def NET_IPXSocket():
    return None


def NET_OpenIPX():
    return


def NET_Config(multiplayer):
    return


def NET_Sleep(msec):
    return


def NET_Init():
    return


def NET_Shutdown():
    return


def NET_ErrorString():
    return ''
