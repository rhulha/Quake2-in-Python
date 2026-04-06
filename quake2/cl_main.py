import json
import os
import time

from wrapper_qpy.decorators import static_vars


class ClientState:
    def __init__(self):
        self.state = 0                # 0=disconnected,1=connecting,2=connected,3=active
        self.servername = ""
        self.connect_time = 0.0
        self.last_packet_time = 0.0
        self.paused = False
        self.demorecording = False
        self.demofile = None
        self.reliable_commands = []
        self.cmd_queue = []
        self.framecount = 0
        self.frametime = 0.0
        self.download_queue = []
        self.configstrings = {}
        self.baselines = {}
        self.userinfo = {
            "name": "player",
            "skin": "male/grunt",
            "rate": "25000",
            "msg": "1",
            "hand": "0",
            "gender": "male",
        }
        self.net_incoming = []
        self.net_outgoing = []


cls = ClientState()


def _now():
    return time.time()


def _cfg_path():
    return "config_client.json"


def CL_WriteDemoMessage():
    if not cls.demorecording or not cls.demofile:
        return
    msg = {
        "time": _now(),
        "commands": list(cls.cmd_queue),
    }
    cls.demofile.write((json.dumps(msg) + "\n").encode("utf-8"))


def CL_Stop_f():
    if not cls.demorecording:
        return
    cls.demorecording = False
    if cls.demofile:
        cls.demofile.close()
        cls.demofile = None


def CL_Record_f(filename="demo.q2demo"):
    if cls.demorecording:
        return
    cls.demofile = open(filename, "wb")
    cls.demorecording = True


def Cmd_ForwardToServer(command=""):
    if cls.state < 2:
        return
    if command:
        cls.reliable_commands.append(command)


def CL_ForwardToServer_f(command=""):
    Cmd_ForwardToServer(command)


def CL_Pause_f(toggle=True):
    if toggle is True:
        cls.paused = not cls.paused
    else:
        cls.paused = bool(toggle)


def CL_Quit_f():
    CL_Shutdown()


def CL_Drop():
    cls.state = 0
    cls.servername = ""
    cls.reliable_commands = []
    cls.cmd_queue = []
    cls.net_incoming = []
    cls.net_outgoing = []


def CL_SendConnectPacket():
    if not cls.servername:
        return
    cls.net_outgoing.append({
        "type": "connect",
        "server": cls.servername,
        "userinfo": dict(cls.userinfo),
        "time": _now(),
    })


def CL_CheckForResend():
    if cls.state != 1:
        return
    if (_now() - cls.connect_time) >= 3.0:
        cls.connect_time = _now()
        CL_SendConnectPacket()


def CL_Connect_f(servername="localhost"):
    cls.servername = servername
    cls.state = 1
    cls.connect_time = _now()
    CL_SendConnectPacket()


def CL_Rcon_f(command=""):
    if not command:
        return
    cls.net_outgoing.append({"type": "rcon", "command": command, "time": _now()})


def CL_ClearState():
    cls.configstrings = {}
    cls.baselines = {}
    cls.download_queue = []
    cls.framecount = 0


def CL_Disconnect():
    if cls.state == 0:
        return
    cls.net_outgoing.append({"type": "disconnect", "time": _now()})
    CL_Drop()


def CL_Disconnect_f():
    CL_Disconnect()


def CL_Packet_f(packet=None):
    if packet is not None:
        cls.net_incoming.append(packet)


def CL_Changing_f():
    cls.state = 2
    CL_ClearState()


def CL_Reconnect_f():
    if not cls.servername:
        return
    CL_Disconnect()
    CL_Connect_f(cls.servername)


def CL_ParseStatusMessage(msg=None):
    if msg is None:
        return {}
    return {"status": str(msg)}


def CL_PingServers_f(servers=None):
    if servers is None:
        servers = ["localhost"]
    for s in servers:
        cls.net_outgoing.append({"type": "ping", "server": s, "time": _now()})


def CL_Skins_f():
    cls.net_outgoing.append({"type": "skins", "time": _now()})


def CL_ConnectionlessPacket(packet=None):
    if not packet:
        return
    cmd = packet.get("cmd", "") if isinstance(packet, dict) else ""
    if cmd == "client_connect_ok":
        cls.state = 2
    elif cmd == "print":
        text = packet.get("text", "")
        if text:
            print(text)
    elif cmd == "status":
        CL_ParseStatusMessage(packet.get("text", ""))


def CL_DumpPackets():
    dumped = list(cls.net_incoming)
    cls.net_incoming = []
    return dumped


def CL_ReadPackets():
    packets = CL_DumpPackets()
    for p in packets:
        if isinstance(p, dict) and p.get("connectionless"):
            CL_ConnectionlessPacket(p)
            continue
        cls.last_packet_time = _now()
        if cls.state == 2:
            cls.state = 3


def CL_FixUpGender():
    gender = cls.userinfo.get("gender", "")
    if gender not in ("male", "female", "none"):
        cls.userinfo["gender"] = "male"


def CL_Userinfo_f(new_values=None):
    if isinstance(new_values, dict):
        cls.userinfo.update(new_values)
    CL_FixUpGender()
    return dict(cls.userinfo)


def CL_Snd_Restart_f():
    try:
        from .snd_dma import S_Shutdown, S_Init
        S_Shutdown()
        S_Init()
    except Exception:
        return


def CL_RequestNextDownload():
    if not cls.download_queue:
        return
    asset = cls.download_queue.pop(0)
    cls.net_outgoing.append({"type": "download", "asset": asset, "time": _now()})


def CL_Precache_f(assets=None):
    if assets is None:
        assets = []
    cls.download_queue.extend(list(assets))
    CL_RequestNextDownload()


def CL_InitLocal():
    CL_ClearState()
    cfg = _cfg_path()
    if os.path.exists(cfg):
        try:
            with open(cfg, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    cls.userinfo.update(data.get("userinfo", {}))
        except Exception:
            return


def CL_WriteConfiguration():
    data = {"userinfo": cls.userinfo}
    with open(_cfg_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def CL_FixCvarCheats():
    return


def CL_SendCommandToServer(cmd):
    cls.cmd_queue.append(cmd)


def CL_SendCommand():
    if cls.state < 2:
        return

    try:
        from .cl_input import CL_SendCmd
        cmd = CL_SendCmd()
        if cmd is not None:
            CL_SendCommandToServer(cmd)
    except Exception:
        return

    while cls.reliable_commands:
        r = cls.reliable_commands.pop(0)
        cls.net_outgoing.append({"type": "cmd", "text": r, "time": _now()})


def CL_Frame(msec=0):
    if cls.paused:
        return

    cls.frametime = float(msec) / 1000.0 if msec else 0.0

    # Update input system with correct frametime
    try:
        from .cl_input import _State
        _State.frametime = cls.frametime
    except:
        pass

    CL_CheckForResend()
    CL_ReadPackets()
    CL_SendCommand()

    try:
        from .cl_view import V_RenderView
        V_RenderView(fov_x=90.0, width=800, height=600)
    except Exception:
        return

    if cls.demorecording:
        CL_WriteDemoMessage()

    cls.framecount += 1


def CL_Init():
    CL_InitLocal()
    cls.state = 0


@static_vars(isdown=False)
def CL_Shutdown():
    if CL_Shutdown.isdown:
        print("recursive shutdown")
        return
    CL_Shutdown.isdown = True

    try:
        CL_Stop_f()
    except Exception:
        return

    try:
        CL_WriteConfiguration()
    except Exception:
        return

    CL_Drop()
    CL_Shutdown.isdown = False
