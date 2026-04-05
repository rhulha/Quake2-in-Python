from wrapper_qpy.decorators import va_args2, va_args
from wrapper_qpy.linker import LinkEmptyFunctions


LinkEmptyFunctions(globals(), [])

CS_FREE = 0
CS_ZOMBIE = 1
CS_CONNECTED = 2
CS_SPAWNED = 3

SVC_DISCONNECT = 7
SVC_SOUND = 9
SVC_PRINT = 10
SVC_STUFFTEXT = 11

PRINT_HIGH = 2
CHAN_RELIABLE = 16
ATTN_NONE = 0

RATE_MESSAGES = 32


def _get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _set(obj, name, value):
    if isinstance(obj, dict):
        obj[name] = value
    else:
        setattr(obj, name, value)


def _iter_clients():
    try:
        from .sv_main import server
    except Exception:
        return []
    clients = _get(server, 'clients', [])
    return clients if clients else []


def _client_message_buffer(client):
    netchan = _get(client, 'netchan', None)
    if netchan is None:
        return None
    if isinstance(netchan, dict):
        return netchan.get('message')
    return getattr(netchan, 'message', None)


def _queue_print(client, level, string):
    msgbuf = _client_message_buffer(client)
    if msgbuf is not None:
        try:
            from .common import MSG_WriteByte, MSG_WriteString
            MSG_WriteByte(msgbuf, SVC_PRINT)
            MSG_WriteByte(msgbuf, int(level))
            MSG_WriteString(msgbuf, str(string))
            return
        except Exception:
            pass

    events = _get(client, 'out_events', None)
    if events is None:
        events = []
        _set(client, 'out_events', events)
    events.append({'type': 'print', 'level': int(level), 'text': str(string)})


def SV_FlushRedirect(sv_redirected, outputbug):
    try:
        from .sv_main import server
    except Exception:
        return

    if sv_redirected == 2:  # RD_PACKET
        packets = _get(server, 'oob_packets', None)
        if packets is None:
            packets = []
            _set(server, 'oob_packets', packets)
        packets.append({'type': 'print', 'text': str(outputbug)})
        return

    if sv_redirected == 1:  # RD_CLIENT
        client = _get(server, 'current_client', None)
        if client is not None:
            _queue_print(client, PRINT_HIGH, outputbug)


@va_args2(2)
def SV_ClientPrintf(cl, level, string):
    if cl is None:
        return
    if int(level) < int(_get(cl, 'messagelevel', 0)):
        return
    _queue_print(cl, level, string)


@va_args2(1)
def SV_BroadcastPrintf(level, string):
    text = str(string)
    try:
        from .common import Com_Printf
        Com_Printf('%s', text)
    except Exception:
        print(text, end='')

    for cl in _iter_clients():
        state = int(_get(cl, 'state', CS_FREE))
        if state != CS_SPAWNED:
            continue
        if int(level) < int(_get(cl, 'messagelevel', 0)):
            continue
        _queue_print(cl, level, text)


@va_args
def SV_BroadcastCommand(string):
    text = str(string)
    for cl in _iter_clients():
        state = int(_get(cl, 'state', CS_FREE))
        if state in (CS_FREE, CS_ZOMBIE):
            continue
        msgbuf = _client_message_buffer(cl)
        if msgbuf is not None:
            try:
                from .common import MSG_WriteByte, MSG_WriteString
                MSG_WriteByte(msgbuf, SVC_STUFFTEXT)
                MSG_WriteString(msgbuf, text)
                continue
            except Exception:
                pass
        events = _get(cl, 'out_events', None)
        if events is None:
            events = []
            _set(cl, 'out_events', events)
        events.append({'type': 'stufftext', 'text': text})


def SV_Multicast(origin, _to):
    try:
        from .sv_main import server
    except Exception:
        return

    payload = _get(server, 'multicast_payload', None)
    if payload is None:
        payload = []
        _set(server, 'multicast_payload', payload)

    reliable = int(_to) in (3, 4, 5)  # *_R variants

    for cl in _iter_clients():
        state = int(_get(cl, 'state', CS_FREE))
        if state in (CS_FREE, CS_ZOMBIE):
            continue
        if state != CS_SPAWNED and not reliable:
            continue
        key = 'reliable_datagram' if reliable else 'datagram'
        out = _get(cl, key, None)
        if out is None:
            out = []
            _set(cl, key, out)
        out.extend(payload)

    _set(server, 'multicast_payload', [])


def SV_StartSound(origin, entity, channel, soundindex, volume, attentuation, timeofs):
    try:
        from .sv_main import server
    except Exception:
        return

    payload = _get(server, 'multicast_payload', None)
    if payload is None:
        payload = []
        _set(server, 'multicast_payload', payload)

    payload.append({
        'type': 'sound',
        'origin': origin,
        'entity': entity,
        'channel': int(channel),
        'soundindex': int(soundindex),
        'volume': float(volume),
        'attenuation': float(attentuation),
        'timeofs': float(timeofs),
    })

    if int(channel) & CHAN_RELIABLE:
        multicast_to = 4 if float(attentuation) != ATTN_NONE else 3
    else:
        multicast_to = 1 if float(attentuation) != ATTN_NONE else 0
    SV_Multicast(origin, multicast_to)


def SV_SendClientDatagram(client):
    if client is None:
        return False

    if SV_RateDrop(client):
        return False

    frames = _get(client, 'frames', None)
    if frames is None:
        frames = []
        _set(client, 'frames', frames)

    frame = {
        'server_time': _get(client, 'server_time', 0),
        'datagram': list(_get(client, 'datagram', [])),
    }
    frames.append(frame)
    _set(client, 'datagram', [])

    ring = _get(client, 'message_size', None)
    if ring is None:
        ring = [0] * RATE_MESSAGES
        _set(client, 'message_size', ring)
    framenum = int(_get(client, 'framenum', 0))
    ring[framenum % RATE_MESSAGES] = len(frame['datagram'])
    _set(client, 'framenum', framenum + 1)
    return True


def SV_DemoCompleted():
    try:
        from .sv_main import server
    except Exception:
        return

    demofile = _get(server, 'demofile', None)
    if demofile:
        try:
            demofile.close()
        except Exception:
            pass
        _set(server, 'demofile', None)

    try:
        from .sv_user import SV_Nextserver
        SV_Nextserver()
    except Exception:
        pass


def SV_RateDrop(c):
    netchan = _get(c, 'netchan', None)
    remote_type = None
    if isinstance(netchan, dict):
        remote = netchan.get('remote_address')
        if isinstance(remote, dict):
            remote_type = remote.get('type')
    elif netchan is not None:
        remote = getattr(netchan, 'remote_address', None)
        if remote is not None:
            remote_type = getattr(remote, 'type', None)
    if remote_type == 0:  # NA_LOOPBACK
        return False

    ring = _get(c, 'message_size', None)
    if not ring:
        return False

    total = sum(int(x) for x in ring)
    rate = int(_get(c, 'rate', 25000))
    if total > rate:
        _set(c, 'surpressCount', int(_get(c, 'surpressCount', 0)) + 1)
        framenum = int(_get(c, 'framenum', 0))
        ring[framenum % RATE_MESSAGES] = 0
        return True
    return False


def SV_SendClientMessages():
    try:
        from .sv_main import SV_DropClient
    except Exception:
        return

    for c in _iter_clients():
        state = int(_get(c, 'state', CS_FREE))
        if state == CS_FREE:
            continue

        msgbuf = _client_message_buffer(c)
        if msgbuf is not None and _get(msgbuf, 'overflowed', False):
            try:
                from .common import SZ_Clear
                SZ_Clear(msgbuf)
            except Exception:
                pass
            _set(c, 'datagram', [])
            SV_DropClient(c)
            _set(c, 'state', CS_ZOMBIE)
            continue

        if state != CS_SPAWNED:
            continue

        SV_SendClientDatagram(c)


