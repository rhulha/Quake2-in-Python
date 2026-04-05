"""
sv_main.py - Quake 2 server implementation
Handles server initialization, frame execution, and client management
"""

from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error", "Cvar_Get", "Cmd_AddCommand"])

# ===== Server State =====

class Server:
    def __init__(self):
        self.state = 0                  # 0=not running, 1=loading, 2=running
        self.mapname = ""
        self.models = []
        self.edicts = []
        self.num_edicts = 0
        self.max_edicts = 1024
        self.time = 0.0
        self.frametime = 0.001
        self.entities = []


server = Server()

CS_FREE = 0
CS_ZOMBIE = 1
CS_CONNECTED = 2
CS_SPAWNED = 3


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
    clients = _get(server, 'clients', None)
    if clients is None:
        clients = []
        _set(server, 'clients', clients)
    return clients

# ===== Initialization =====

def SV_Init():
    """Initialize server"""
    try:
        from .common import Com_Printf, Cvar_Get, Cmd_AddCommand

        Com_Printf("SV_Init()\n")

        # Register server cvars
        sv_gravity = Cvar_Get("sv_gravity", "800", 0)
        sv_friction = Cvar_Get("sv_friction", "6", 0)
        sv_stopspeed = Cvar_Get("sv_stopspeed", "100", 0)

        # Initialize entity list
        server.edicts = [None] * server.max_edicts
        server.num_edicts = 0

        # Register server commands
        Cmd_AddCommand("map", SV_Map_f)
        Cmd_AddCommand("killserver", SV_KillServer_f)

        Com_Printf("SV_Init complete\n")
        return True

    except Exception as e:
        print(f"SV_Init error: {e}")
        return False


def SV_Shutdown(message, reconnect=False):
    """Shutdown server"""
    try:
        from .common import Com_Printf

        Com_Printf(f"SV_Shutdown: {message}\n")

        server.state = 0
        server.edicts = []
        server.num_edicts = 0

    except Exception as e:
        print(f"SV_Shutdown error: {e}")


# ===== Frame Execution =====

def SV_Frame(msec):
    """
    Main server frame.
    Called once per frame to update all entities and physics.
    """
    try:
        from .common import Com_Printf
        from .cmodel import CM_LoadMap

        if server.state == 0:
            return

        # Update frame time
        server.frametime = msec / 1000.0
        server.time += server.frametime

        # Run game frame
        try:
            from game import G_RunFrame
            G_RunFrame()
        except Exception as e:
            Com_Printf(f"Game frame error: {e}\n")

        # Send messages to clients
        try:
            SV_SendClientMessages()
        except:
            pass

    except Exception as e:
        print(f"SV_Frame error: {e}")


def SV_RunGameFrame():
    """Run game logic frame"""
    try:
        # Call game DLL frame
        from game import G_RunFrame

        G_RunFrame()

    except Exception as e:
        print(f"SV_RunGameFrame error: {e}")


# ===== Map Loading =====

def SV_Map_f():
    """map <mapname> - Load a map"""
    try:
        from .cmd import Cmd_Argc, Cmd_Argv
        from .common import Com_Printf, Com_Error
        from .cmodel import CM_LoadMap
        from game import G_SpawnEntities

        if Cmd_Argc() < 2:
            Com_Printf("Usage: map <mapname>\n")
            return

        mapname = Cmd_Argv(1)

        # Load collision model
        try:
            CM_LoadMap(f"maps/{mapname}.bsp", False, None)
        except Exception as e:
            Com_Error(0, f"Couldn't load map {mapname}: {e}")
            return

        # Load game
        try:
            from game.g_main import G_Init
            G_Init()
        except Exception as e:
            Com_Printf(f"Note: Game logic not available: {e}\n")

        # Spawn entities from map
        try:
            G_SpawnEntities(mapname)
        except Exception as e:
            Com_Printf(f"Note: Entity spawning not available: {e}\n")

        server.state = 2  # Running
        server.mapname = mapname
        server.time = 0.0

        Com_Printf(f"Loaded map: {mapname}\n")

    except Exception as e:
        print(f"SV_Map_f error: {e}")


def SV_KillServer_f():
    """killserver - Stop the server"""
    SV_Shutdown("Server terminated", False)


# ===== Entity Management =====

def SV_SpawnEntity():
    """Allocate a new entity"""
    if server.num_edicts >= server.max_edicts:
        return None

    edict = {
        'number': server.num_edicts,
        'inuse': False,
        'classname': '',
        'model': '',
        'origin': [0, 0, 0],
        'angles': [0, 0, 0],
        'velocity': [0, 0, 0],
        'solid': 0,
        'svflags': 0,
        'owner': None,
        'think': None,
        'nextthink': 0,
        'health': 0,
    }

    server.edicts[server.num_edicts] = edict
    server.num_edicts += 1

    return edict


def SV_LinkEntity(ent):
    """Link entity into world (for collision)"""
    linked = _get(server, 'linked_entities', None)
    if linked is None:
        linked = []
        _set(server, 'linked_entities', linked)
    if ent not in linked:
        linked.append(ent)


def SV_UnlinkEntity(ent):
    """Unlink entity from world"""
    linked = _get(server, 'linked_entities', [])
    if ent in linked:
        linked.remove(ent)


def SV_TouchTriggers(ent):
    """Check for trigger touches"""
    linked = _get(server, 'linked_entities', [])
    touch = _get(ent, 'touch', None)
    for other in linked:
        if other is ent:
            continue
        if _get(other, 'classname', '').startswith('trigger_') and touch:
            try:
                touch(ent, other, None, None)
            except Exception:
                continue


# ===== Client Management =====

def SV_DropClient(drop):
    """Drop a client connection"""
    if drop is None:
        return

    try:
        from .common import MSG_WriteByte
        msg = _get(_get(drop, 'netchan', {}), 'message', None)
        if msg is not None:
            MSG_WriteByte(msg, 7)  # svc_disconnect
    except Exception:
        pass

    if int(_get(drop, 'state', CS_FREE)) == CS_SPAWNED:
        try:
            from game.p_client import ClientDisconnect
            edict = _get(drop, 'edict', None)
            if edict is not None:
                ClientDisconnect(edict)
        except Exception:
            pass

    download = _get(drop, 'download', None)
    if download:
        try:
            download.close()
        except Exception:
            pass
        _set(drop, 'download', None)

    _set(drop, 'state', CS_ZOMBIE)
    _set(drop, 'name', '')


def SV_SendClientMessages():
    """Send state updates to connected clients"""
    try:
        from .sv_send import SV_SendClientMessages as _send
        _send()
    except Exception:
        pass


def SV_ExecuteUserCommand(s):
    """Execute a user command"""
    try:
        from .sv_user import SV_ExecuteUserCommand as _exec
        _exec(s)
    except Exception:
        pass


# ===== Network Commands (Server-side) =====

def SVC_Status():
    """Handle status query"""
    try:
        from .common import Com_Printf
        Com_Printf('SVC_Status\n%s\n', SV_StatusString())
    except Exception:
        return


def SVC_Ack():
    """Handle acknowledgment"""
    try:
        from .common import Com_Printf
        Com_Printf('Ping acknowledge\n')
    except Exception:
        return


def SVC_Info():
    """Handle info query"""
    info = {
        'hostname': _get(server, 'hostname', 'Quake2Python'),
        'map': _get(server, 'mapname', ''),
        'clients': len([c for c in _iter_clients() if int(_get(c, 'state', 0)) >= CS_CONNECTED]),
        'maxclients': int(_get(server, 'maxclients', 1)),
    }
    _set(server, 'last_info_reply', info)


def SVC_Ping():
    """Handle ping"""
    _set(server, 'last_ping_reply', 'ack')


def SVC_GetChallenge():
    """Handle challenge request"""
    challenges = _get(server, 'challenges', None)
    if challenges is None:
        challenges = []
        _set(server, 'challenges', challenges)
    challenge = len(challenges) + 1
    challenges.append(challenge)
    _set(server, 'last_challenge', challenge)


def SVC_DirectConnect():
    """Handle direct connection"""
    clients = _iter_clients()
    for cl in clients:
        if int(_get(cl, 'state', CS_FREE)) in (CS_FREE, CS_ZOMBIE):
            _set(cl, 'state', CS_CONNECTED)
            _set(cl, 'lastmessage', int(_get(server, 'realtime', 0)))
            return

    clients.append({
        'state': CS_CONNECTED,
        'lastmessage': int(_get(server, 'realtime', 0)),
        'name': 'player',
        'messagelevel': 0,
        'rate': 25000,
        'message_size': [0] * 32,
        'framenum': 0,
    })


def SV_StatusString():
    """Get server status string"""
    lines = []
    lines.append(f'map:{_get(server, "mapname", "")} state:{_get(server, "state", 0)}')
    for cl in _iter_clients():
        state = int(_get(cl, 'state', CS_FREE))
        if state in (CS_CONNECTED, CS_SPAWNED):
            score = _get(_get(_get(cl, 'edict', None), 'client', None), 'resp', None)
            frags = _get(score, 'score', 0)
            ping = int(_get(cl, 'ping', 0))
            name = _get(cl, 'name', '')
            lines.append(f'{frags} {ping} "{name}"')
    return '\n'.join(lines)


def Rcon_Validate():
    """Validate remote console command"""
    password = str(_get(server, 'rcon_password', ''))
    provided = str(_get(server, 'rcon_provided', ''))
    return bool(password) and password == provided


# ===== Utilities =====

def SV_CheckTimeouts():
    """Check for client timeouts"""
    realtime = int(_get(server, 'realtime', 0))
    timeout = int(_get(server, 'timeout_ms', 120000))
    zombie_timeout = int(_get(server, 'zombie_ms', 2000))
    droppoint = realtime - timeout
    zombiepoint = realtime - zombie_timeout

    for cl in _iter_clients():
        lastmessage = int(_get(cl, 'lastmessage', realtime))
        if lastmessage > realtime:
            lastmessage = realtime
            _set(cl, 'lastmessage', lastmessage)

        state = int(_get(cl, 'state', CS_FREE))
        if state == CS_ZOMBIE and lastmessage < zombiepoint:
            _set(cl, 'state', CS_FREE)
            continue
        if state in (CS_CONNECTED, CS_SPAWNED) and lastmessage < droppoint:
            try:
                from .sv_send import SV_BroadcastPrintf
                SV_BroadcastPrintf(2, f'{_get(cl, "name", "client")} timed out\n')
            except Exception:
                pass
            SV_DropClient(cl)
            _set(cl, 'state', CS_FREE)


def SV_CalculatePing(client):
    """Calculate client ping"""
    return 0


def SV_WriteFrame(msg):
    if isinstance(msg, dict):
        msg['server_time'] = server.time
        msg['entities'] = [e for e in server.edicts if e]


def SV_Multicast(origin, to):
    try:
        from .sv_send import SV_Multicast as _multicast
        _multicast(origin, to)
    except Exception:
        pass


def SV_StartSound(origin, ent, channel, soundindex, volume, attenuation):
    try:
        from .sv_send import SV_StartSound as _startsound
        _startsound(origin, ent, channel, soundindex, volume, attenuation, 0.0)
    except Exception:
        pass


def SV_BroadcastCommand(fmt):
    try:
        from .sv_send import SV_BroadcastCommand as _broadcast
        _broadcast(fmt)
    except Exception:
        pass


def SV_BroadcastPrintf(fmt):
    try:
        from .sv_send import SV_BroadcastPrintf as _broadcast
        _broadcast(2, fmt)
    except Exception:
        pass

