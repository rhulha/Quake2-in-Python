import math
import random

from .reference_import import gi


def _game():
    from .g_main import game
    return game


_body_que = []


def SP_FixCoopSpots(_self=None):
    return


def SP_CreateCoopSpots(_self=None):
    return


def SP_info_player_start(_self):
    return


def SP_info_player_deathmatch(_self):
    return


def SP_info_player_coop(_self):
    return


def SP_info_player_intermission(_self):
    return


def player_pain(self, other, kick, damage):
    if self.health <= 0:
        return
    if gi.sound and gi.soundindex:
        gi.sound(self, 1, gi.soundindex("*pain100_1.wav"), 1, 1, 0)


def IsFemale(ent):
    if not ent or not ent.client:
        return False
    skin = ent.client.pers.userinfo.get("skin", "")
    return "female" in skin.lower()


def IsNeutral(ent):
    if not ent or not ent.client:
        return True
    skin = ent.client.pers.userinfo.get("skin", "")
    s = skin.lower()
    return ("male" not in s) and ("female" not in s)


def ClientObituary(self, inflictor, attacker):
    if not self or not self.client:
        return
    name = self.client.pers.netname or "player"
    if gi.bprintf:
        gi.bprintf(2, f"{name} died.\n")


def TossClientWeapon(self):
    if not self.client:
        return
    weap = self.client.pers.weapon
    if not weap:
        return
    try:
        from .p_weapon import Drop_Weapon
        Drop_Weapon(self, weap)
    except Exception:
        return


def LookAtKiller(self, inflictor, attacker):
    if not attacker:
        return
    dx = attacker.s.origin[0] - self.s.origin[0]
    dy = attacker.s.origin[1] - self.s.origin[1]
    if dx == 0 and dy == 0:
        return
    self.client.killer_yaw = math.degrees(math.atan2(dy, dx))


def player_die(self, inflictor, attacker, damage, point):
    self.takedamage = 0
    self.movetype = 0
    self.svflags |= 0x20
    self.deadflag = 1
    self.health = max(-999, self.health)
    ClientObituary(self, inflictor, attacker)
    TossClientWeapon(self)
    LookAtKiller(self, inflictor, attacker)


def InitClientPersistant(client):
    client.pers.health = 100
    client.pers.max_health = 100
    client.pers.connected = True
    if not client.pers.netname:
        client.pers.netname = "player"

    try:
        from .g_items import FindItem
        blaster = FindItem("Blaster")
        if blaster:
            client.pers.weapon = blaster
            client.pers.inventory[blaster.index] = 1
    except Exception:
        return


def InitClientResp(client):
    client.resp.enterframe = getattr(_game().level, "framenum", 0)
    client.resp.score = 0
    client.resp.spectator = False


def SaveClientData():
    game = _game()
    for ent in getattr(game, "entities", []):
        if not ent or not getattr(ent, "inuse", False) or not ent.client:
            continue
        ent.client.pers.health = ent.health
        ent.client.pers.max_health = ent.max_health


def FetchClientEntData(ent):
    if not ent or not ent.client:
        return
    ent.health = ent.client.pers.health
    ent.max_health = ent.client.pers.max_health


def PlayersRangeFromSpot(spot):
    game = _game()
    best = 999999.0
    for ent in game.entities:
        if not ent or not ent.inuse or not ent.client:
            continue
        dx = ent.s.origin[0] - spot.s.origin[0]
        dy = ent.s.origin[1] - spot.s.origin[1]
        dz = ent.s.origin[2] - spot.s.origin[2]
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d < best:
            best = d
    return best


def SelectRandomDeathmatchSpawnPoint():
    from .g_utils import G_Find
    spots = []
    ent = None
    while True:
        ent = G_Find(ent, "classname", "info_player_deathmatch")
        if not ent:
            break
        spots.append(ent)
    if not spots:
        return None
    return random.choice(spots)


def SelectFarthestDeathmatchSpawnPoint():
    from .g_utils import G_Find
    bestspot = None
    bestdist = -1.0
    ent = None
    while True:
        ent = G_Find(ent, "classname", "info_player_deathmatch")
        if not ent:
            break
        d = PlayersRangeFromSpot(ent)
        if d > bestdist:
            bestdist = d
            bestspot = ent
    return bestspot


def SelectDeathmatchSpawnPoint():
    spot = SelectFarthestDeathmatchSpawnPoint()
    if not spot:
        spot = SelectRandomDeathmatchSpawnPoint()
    return spot


def SelectCoopSpawnPoint(ent):
    from .g_utils import G_Find
    return G_Find(None, "classname", "info_player_coop")


def SelectSpawnPoint(ent, origin, angles):
    from .g_utils import G_Find
    game = _game()
    spot = None
    if getattr(game, "deathmatch", False):
        spot = SelectDeathmatchSpawnPoint()
    elif getattr(game, "coop", False):
        spot = SelectCoopSpawnPoint(ent)
    if not spot:
        spot = G_Find(None, "classname", "info_player_start")
    if not spot:
        spot = ent

    origin[:] = list(spot.s.origin)
    origin[2] += 9
    angles[:] = list(spot.s.angles)
    return spot


def InitBodyQue():
    global _body_que
    _body_que = []
    game = _game()
    from .g_utils import G_Spawn
    for _ in range(8):
        body = G_Spawn()
        body.classname = "bodyque"
        _body_que.append(body)
    game.body_que = 0


def body_die(self, inflictor, attacker, damage, point):
    return


def CopyToBodyQue(ent):
    game = _game()
    if not _body_que:
        return
    idx = getattr(game, "body_que", 0) % len(_body_que)
    body = _body_que[idx]
    game.body_que = idx + 1

    body.s = ent.s
    body.svflags = ent.svflags
    body.mins[:] = list(ent.mins)
    body.maxs[:] = list(ent.maxs)
    body.absmin[:] = list(ent.absmin)
    body.absmax[:] = list(ent.absmax)
    body.velocity[:] = list(ent.velocity)
    body.avelocity[:] = list(ent.avelocity)
    body.movetype = ent.movetype
    body.solid = ent.solid
    body.clipmask = ent.clipmask
    body.takedamage = 0
    body.deadflag = 1
    body.die = body_die
    if gi.linkentity:
        gi.linkentity(body)


def respawn(self):
    CopyToBodyQue(self)
    PutClientInServer(self)
    self.s.event = 2


def spectator_respawn(ent):
    PutClientInServer(ent)


def PutClientInServer(ent):
    if not ent or not ent.client:
        return

    spawn_origin = [0.0, 0.0, 0.0]
    spawn_angles = [0.0, 0.0, 0.0]
    SelectSpawnPoint(ent, spawn_origin, spawn_angles)

    ent.movetype = 3
    ent.solid = 3
    ent.clipmask = 0x1
    ent.s.modelindex = 255
    ent.deadflag = 0
    ent.svflags &= ~0x20
    ent.mins[:] = [-16, -16, -24]
    ent.maxs[:] = [16, 16, 32]
    ent.s.origin[:] = list(spawn_origin)
    ent.s.angles[:] = [0, spawn_angles[1], 0]
    ent.velocity[:] = [0.0, 0.0, 0.0]
    ent.viewheight = 22
    ent.takedamage = 1
    ent.pain = player_pain
    ent.die = player_die
    ent.health = ent.client.pers.health if ent.client.pers.health else 100
    ent.max_health = ent.client.pers.max_health if ent.client.pers.max_health else 100

    ent.client.ps.pmove.origin[:] = [int(spawn_origin[i] * 8) for i in range(3)]
    ent.client.ps.pmove.velocity[:] = [0, 0, 0]
    ent.client.ps.viewangles[:] = list(ent.s.angles)
    ent.client.v_angle[:] = list(ent.s.angles)
    ent.client.weaponstate = 0

    if gi.linkentity:
        gi.linkentity(ent)


def ClientBeginDeathmatch(ent):
    InitClientResp(ent.client)
    PutClientInServer(ent)
    if gi.bprintf:
        gi.bprintf(2, f"{ent.client.pers.netname} entered the game\n")


def ClientBegin(ent):
    game = _game()
    if getattr(game, "deathmatch", False):
        ClientBeginDeathmatch(ent)
        return
    PutClientInServer(ent)


def ClientUserinfoChanged(ent, userinfo):
    if not ent or not ent.client:
        return
    if isinstance(userinfo, dict):
        ent.client.pers.userinfo.update(userinfo)

    name = ent.client.pers.userinfo.get("name", "player")
    if len(name) > 15:
        name = name[:15]
    ent.client.pers.netname = name


def ClientConnect(ent, userinfo):
    if not ent.client:
        from shared.QClasses import gclient_t
        ent.client = gclient_t()
    InitClientPersistant(ent.client)
    InitClientResp(ent.client)
    ClientUserinfoChanged(ent, userinfo if isinstance(userinfo, dict) else {})
    if gi.bprintf:
        gi.bprintf(2, f"{ent.client.pers.netname} connected\n")
    return True


def ClientDisconnect(ent):
    if not ent:
        return
    if gi.bprintf and ent.client:
        gi.bprintf(2, f"{ent.client.pers.netname} disconnected\n")
    if gi.unlinkentity:
        gi.unlinkentity(ent)
    ent.s.modelindex = 0
    ent.inuse = False
    ent.classname = "disconnected"
    ent.client = None


def PM_trace(start, mins, maxs, end):
    if gi.trace:
        return gi.trace(start, mins, maxs, end, None, 0x1)
    return None


def CheckBlock(_self, _other):
    return False


def PrintPmove(pmove):
    return f"pmove origin={pmove.origin} vel={pmove.velocity}"


def ClientThink(ent, ucmd):
    if not ent:
        return

    is_dict = isinstance(ent, dict)
    client = ent.get('client') if is_dict else getattr(ent, 'client', None)
    if not client:
        return

    if is_dict:
        ent['client']['oldbuttons'] = ent['client'].get('buttons', 0)
        ent['client']['buttons'] = getattr(ucmd, "buttons", 0)
    else:
        ent.client.oldbuttons = ent.client.buttons
        ent.client.buttons = getattr(ucmd, "buttons", 0)

    health = ent.get('health', 100) if is_dict else getattr(ent, 'health', 100)
    if health <= 0:
        return

    if hasattr(ucmd, "angles"):
        if is_dict:
            if 'client' in ent and 'v_angle' in ent['client']:
                ent['client']['v_angle'][:] = list(ucmd.angles)
        else:
            ent.client.v_angle[:] = list(ucmd.angles)

    velocity = ent.get('velocity') if is_dict else getattr(ent, 'velocity', None)
    if velocity:
        if hasattr(ucmd, "forwardmove"):
            velocity[0] = float(ucmd.forwardmove)
        if hasattr(ucmd, "sidemove"):
            velocity[1] = float(ucmd.sidemove)
        if hasattr(ucmd, "upmove"):
            velocity[2] = float(ucmd.upmove)

    try:
        from .p_weapon import Think_Weapon
        Think_Weapon(ent)
    except Exception:
        return


def ClientBeginServerFrame(ent):
    if not ent or not ent.client:
        return
    if ent.deadflag and getattr(_game().level, "time", 0.0) > ent.client.respawn_time:
        if ent.client.buttons & 1:
            respawn(ent)
