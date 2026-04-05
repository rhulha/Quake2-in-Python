import os

from .sv_main import server, SV_DropClient

sv_client = None
sv_player = None


def SV_BeginDemoserver():
    if not getattr(server, "name", ""):
        return
    demo_name = os.path.join("demos", server.name)
    if os.path.exists(demo_name):
        server.demofile = open(demo_name, "rb")
    else:
        raise RuntimeError(f"Couldn't open {demo_name}")


def SV_New_f():
    global sv_player
    if not sv_client:
        return

    if getattr(sv_client, "state", 0) != 1:
        return

    if getattr(server, "state", 0) == 3:
        SV_BeginDemoserver()
        return

    playernum = getattr(sv_client, "index", -1)
    if getattr(server, "state", 0) in (4, 5):
        playernum = -1

    if getattr(server, "state", 0) == 2 and playernum >= 0 and getattr(server, "edicts", None):
        ent_index = playernum + 1
        if ent_index < len(server.edicts):
            sv_player = server.edicts[ent_index]
            if sv_player:
                sv_player.s.number = ent_index
                sv_client.edict = sv_player


def SV_Configstrings_f():
    if not sv_client:
        return
    if getattr(sv_client, "state", 0) != 1:
        return

    if not hasattr(server, "configstrings"):
        server.configstrings = {}

    if not hasattr(sv_client, "download_pos"):
        sv_client.download_pos = 0

    start = int(getattr(sv_client, "config_start", 0))
    keys = sorted(server.configstrings.keys())

    chunk = []
    max_chunk = 64
    i = 0
    for k in keys:
        if k < start:
            continue
        chunk.append((k, server.configstrings[k]))
        i += 1
        if i >= max_chunk:
            break

    sv_client.pending_configstrings = chunk
    if chunk:
        sv_client.config_start = chunk[-1][0] + 1
    else:
        sv_client.config_start = 0


def SV_Baselines_f():
    if not sv_client:
        return
    if getattr(sv_client, "state", 0) != 1:
        return

    if not hasattr(server, "baselines"):
        server.baselines = {}

    start = int(getattr(sv_client, "baseline_start", 0))
    keys = sorted(server.baselines.keys())

    chunk = []
    max_chunk = 64
    i = 0
    for k in keys:
        if k < start:
            continue
        chunk.append((k, server.baselines[k]))
        i += 1
        if i >= max_chunk:
            break

    sv_client.pending_baselines = chunk
    if chunk:
        sv_client.baseline_start = chunk[-1][0] + 1
    else:
        sv_client.baseline_start = 0


def SV_Begin_f():
    if not sv_client:
        return
    sv_client.state = 2  # spawned
    if sv_player:
        try:
            from game.p_client import ClientBegin
            ClientBegin(sv_player)
        except Exception:
            pass


def SV_NextDownload_f():
    if not sv_client:
        return
    f = getattr(sv_client, "download", None)
    if not f:
        return

    data = f.read(1024)
    if not data:
        f.close()
        sv_client.download = None
        sv_client.download_data = b""
        sv_client.download_percent = 100
        return

    sv_client.download_data = data
    sv_client.downloadcount = getattr(sv_client, "downloadcount", 0) + len(data)
    total = max(1, getattr(sv_client, "downloadsize", sv_client.downloadcount))
    sv_client.download_percent = int((sv_client.downloadcount * 100) / total)


def SV_BeginDownload_f(path=None):
    if not sv_client:
        return

    filename = path or getattr(sv_client, "download_name", "")
    if not filename or ".." in filename:
        return

    if not os.path.exists(filename):
        return

    sv_client.download = open(filename, "rb")
    sv_client.downloadsize = os.path.getsize(filename)
    sv_client.downloadcount = 0
    sv_client.download_name = filename
    SV_NextDownload_f()


def SV_Disconnect_f():
    SV_DropClient(sv_client)


def SV_ShowServerinfo_f():
    if not sv_client:
        return
    sv_client.serverinfo = {
        "mapname": getattr(server, "mapname", ""),
        "state": getattr(server, "state", 0),
        "num_edicts": getattr(server, "num_edicts", 0),
    }


def SV_Nextserver():
    nextserver = getattr(server, "nextserver", "")
    if nextserver:
        try:
            from .sv_init import SV_Map
            SV_Map(False, nextserver, False)
        except Exception:
            pass


def SV_Nextserver_f():
    SV_Nextserver()


def SV_ExecuteUserCommand(command_line=""):
    if not sv_client:
        return
    if not command_line:
        return

    parts = command_line.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "new":
        SV_New_f()
    elif cmd == "configstrings":
        if args:
            sv_client.config_start = int(args[-1])
        SV_Configstrings_f()
    elif cmd == "baselines":
        if args:
            sv_client.baseline_start = int(args[-1])
        SV_Baselines_f()
    elif cmd == "begin":
        SV_Begin_f()
    elif cmd == "nextdl":
        SV_NextDownload_f()
    elif cmd == "download":
        SV_BeginDownload_f(args[0] if args else None)
    elif cmd == "disconnect":
        SV_Disconnect_f()
    elif cmd == "info":
        SV_ShowServerinfo_f()
    elif cmd == "nextserver":
        SV_Nextserver_f()


def SV_ClientThink(cl, cmd):
    if not cl or not getattr(cl, "edict", None):
        return
    cl.lastcmd = cmd
    try:
        from game.p_client import ClientThink
        ClientThink(cl.edict, cmd)
    except Exception:
        pass


def SV_ExecuteClientMessage(cl):
    global sv_client, sv_player
    sv_client = cl
    sv_player = getattr(cl, "edict", None)

    cmds = getattr(cl, "incoming_commands", [])
    for entry in cmds:
        if isinstance(entry, str):
            SV_ExecuteUserCommand(entry)
        elif isinstance(entry, tuple) and len(entry) >= 2:
            if entry[0] == "ucmd":
                SV_ClientThink(cl, entry[1])
    cl.incoming_commands = []
