from functools import cmp_to_key

from .reference_import import gi


IT_WEAPON = 1
IT_AMMO = 2
IT_ARMOR = 4


def _game():
    from .g_main import game
    return game


def _cmd_argv(i):
    if hasattr(gi, "argv") and gi.argv:
        return gi.argv(i)
    return ""


def _cmd_args():
    if hasattr(gi, "args") and gi.args:
        return gi.args()
    return ""


def _cprintf(ent, msg):
    if hasattr(gi, "cprintf") and gi.cprintf:
        gi.cprintf(ent, 2, msg)


def ClientTeam(ent):
    if not ent or not ent.client:
        return ""
    skin = ent.client.pers.userinfo.get("skin", "")
    if "/" not in skin:
        return skin
    model, team = skin.split("/", 1)
    dmflags = int(getattr(_game(), "dmflags", 0))
    if dmflags & 0x00000004:
        return model
    return team


def OnSameTeam(ent1, ent2):
    dmflags = int(getattr(_game(), "dmflags", 0))
    if not (dmflags & (0x00000004 | 0x00000008)):
        return False
    return ClientTeam(ent1) == ClientTeam(ent2)


def SelectNextItem(ent, itflags):
    if not ent or not ent.client:
        return

    cl = ent.client
    items = getattr(_game(), "itemlist", [])
    max_items = min(len(cl.pers.inventory), len(items))
    if max_items == 0:
        cl.pers.selected_item = -1
        return

    start = cl.pers.selected_item if cl.pers.selected_item >= 0 else 0
    for i in range(1, max_items + 1):
        idx = (start + i) % max_items
        if not cl.pers.inventory[idx]:
            continue
        it = items[idx]
        if not it or not it.use:
            continue
        if itflags != -1 and not (it.flags & itflags):
            continue
        cl.pers.selected_item = idx
        return
    cl.pers.selected_item = -1


def SelectPrevItem(ent, itflags):
    if not ent or not ent.client:
        return

    cl = ent.client
    items = getattr(_game(), "itemlist", [])
    max_items = min(len(cl.pers.inventory), len(items))
    if max_items == 0:
        cl.pers.selected_item = -1
        return

    start = cl.pers.selected_item if cl.pers.selected_item >= 0 else 0
    for i in range(1, max_items + 1):
        idx = (start + max_items - i) % max_items
        if not cl.pers.inventory[idx]:
            continue
        it = items[idx]
        if not it or not it.use:
            continue
        if itflags != -1 and not (it.flags & itflags):
            continue
        cl.pers.selected_item = idx
        return
    cl.pers.selected_item = -1


def ValidateSelectedItem(ent):
    if not ent or not ent.client:
        return
    idx = ent.client.pers.selected_item
    if 0 <= idx < len(ent.client.pers.inventory) and ent.client.pers.inventory[idx]:
        return
    SelectNextItem(ent, -1)


def Cmd_Give_f(ent):
    if not ent or not ent.client:
        return
    name = _cmd_args().strip()
    if not name:
        return

    from .g_items import FindItem, SpawnItem, Touch_Item, Add_Ammo
    from .g_utils import G_Spawn, G_FreeEdict

    give_all = name.lower() == "all"

    if give_all or _cmd_argv(1).lower() == "health":
        if _cmd_argv(2):
            ent.health = int(_cmd_argv(2))
        else:
            ent.health = ent.max_health
        if not give_all:
            return

    items = getattr(_game(), "itemlist", [])
    if give_all or name.lower() == "weapons":
        for it in items:
            if it and it.pickup and (it.flags & IT_WEAPON):
                ent.client.pers.inventory[it.index] += 1
        if not give_all:
            return

    if give_all or name.lower() == "ammo":
        for it in items:
            if it and it.pickup and (it.flags & IT_AMMO):
                Add_Ammo(ent, it, 1000)
        if not give_all:
            return

    if give_all:
        for it in items:
            if it and it.pickup and not (it.flags & (IT_ARMOR | IT_WEAPON | IT_AMMO)):
                ent.client.pers.inventory[it.index] = 1
        return

    it = FindItem(name)
    if not it:
        it = FindItem(_cmd_argv(1))
        if not it:
            _cprintf(ent, "unknown item\n")
            return
    if not it.pickup:
        _cprintf(ent, "non-pickup item\n")
        return

    if it.flags & IT_AMMO:
        if _cmd_argv(2):
            ent.client.pers.inventory[it.index] = int(_cmd_argv(2))
        else:
            ent.client.pers.inventory[it.index] += it.quantity
    else:
        it_ent = G_Spawn()
        it_ent.classname = it.classname
        SpawnItem(it_ent, it)
        Touch_Item(it_ent, ent, None, None)
        if it_ent.inuse:
            G_FreeEdict(it_ent)


def Cmd_God_f(ent):
    if not ent:
        return
    ent.flags ^= 0x00000010
    _cprintf(ent, "godmode ON\n" if (ent.flags & 0x00000010) else "godmode OFF\n")


def Cmd_Notarget_f(ent):
    if not ent:
        return
    ent.flags ^= 0x00000020
    _cprintf(ent, "notarget ON\n" if (ent.flags & 0x00000020) else "notarget OFF\n")


def Cmd_Noclip_f(ent):
    if not ent:
        return
    ent.movetype = 8 if ent.movetype != 8 else 3
    _cprintf(ent, "noclip ON\n" if ent.movetype == 8 else "noclip OFF\n")


def Cmd_Use_f(ent):
    if not ent or not ent.client:
        return
    from .g_items import FindItem
    s = _cmd_args().strip()
    it = FindItem(s)
    if not it:
        _cprintf(ent, f"unknown item: {s}\n")
        return
    if not it.use:
        _cprintf(ent, "Item is not usable.\n")
        return
    if ent.client.pers.inventory[it.index] <= 0:
        _cprintf(ent, f"Out of item: {s}\n")
        return
    it.use(ent, it)


def Cmd_Drop_f(ent):
    if not ent or not ent.client:
        return
    from .g_items import FindItem
    s = _cmd_args().strip()
    it = FindItem(s)
    if not it:
        _cprintf(ent, f"unknown item: {s}\n")
        return
    if not it.drop:
        _cprintf(ent, "Item is not dropable.\n")
        return
    if ent.client.pers.inventory[it.index] <= 0:
        _cprintf(ent, f"Out of item: {s}\n")
        return
    it.drop(ent, it)


def Cmd_Inven_f(ent):
    if not ent or not ent.client:
        return
    ent.client.showinventory = not ent.client.showinventory
    ent.client.showhelp = False
    ent.client.showscores = False


def Cmd_InvUse_f(ent):
    if not ent or not ent.client:
        return
    ValidateSelectedItem(ent)
    index = ent.client.pers.selected_item
    if index < 0:
        _cprintf(ent, "No item to use.\n")
        return
    it = _game().itemlist[index]
    if not it or not it.use:
        return
    it.use(ent, it)


def Cmd_WeapPrev_f(ent):
    SelectPrevItem(ent, IT_WEAPON)


def Cmd_WeapNext_f(ent):
    SelectNextItem(ent, IT_WEAPON)


def Cmd_WeapLast_f(ent):
    if not ent or not ent.client:
        return
    if ent.client.pers.lastweapon:
        from .p_weapon import Use_Weapon
        Use_Weapon(ent, ent.client.pers.lastweapon)


def Cmd_InvDrop_f(ent):
    if not ent or not ent.client:
        return
    ValidateSelectedItem(ent)
    index = ent.client.pers.selected_item
    if index < 0:
        return
    it = _game().itemlist[index]
    if it and it.drop:
        it.drop(ent, it)


def Cmd_Kill_f(ent):
    if not ent or ent.health <= 0:
        return
    ent.flags &= ~0x00000010
    ent.health = 0
    if ent.die:
        ent.die(ent, ent, ent, 100000, ent.s.origin)


def Cmd_PutAway_f(ent):
    if not ent or not ent.client:
        return
    ent.client.showinventory = False
    ent.client.showhelp = False
    ent.client.showscores = False


def PlayerSort(a, b):
    a_score = a.client.resp.score if a and a.client else -999999
    b_score = b.client.resp.score if b and b.client else -999999
    if a_score < b_score:
        return 1
    if a_score > b_score:
        return -1
    return 0


def Cmd_Players_f(ent):
    game = _game()
    players = []
    for e in game.entities[1 : game.maxclients + 1]:
        if e and e.inuse and e.client:
            players.append(e)
    players.sort(key=cmp_to_key(PlayerSort))

    lines = []
    for p in players:
        lines.append(f"{p.client.resp.score:3d} {p.client.pers.netname}")

    text = "\n".join(lines)
    if len(text) > 1200:
        text = text[:1200] + "\n..."
    _cprintf(ent, text + "\n")


def Cmd_Wave_f(ent):
    if not ent or not ent.client:
        return
    if ent.client.anim_priority > 1:
        return
    i = int(_cmd_argv(1) or 0)
    ent.client.anim_priority = 1
    ent.s.frame = 0
    ent.client.anim_end = 0
    _cprintf(ent, f"wave {i}\n")


def Cmd_Say_f(ent, team, arg0):
    game = _game()
    msg = _cmd_args()
    if not msg and arg0:
        msg = _cmd_argv(0)
    if not msg:
        return

    prefix = ""
    if ent:
        name = ent.client.pers.netname if ent.client else "console"
        prefix = f"({name}): " if team else f"{name}: "
    text = (prefix + msg).strip()
    if len(text) > 150:
        text = text[:150]

    for other in game.entities[1 : game.maxclients + 1]:
        if not other or not other.inuse or not other.client:
            continue
        if team and ent and not OnSameTeam(ent, other):
            continue
        if gi.cprintf:
            gi.cprintf(other, 2, text + "\n")


def Cmd_PlayerList_f(ent):
    game = _game()
    lines = []
    for i, e in enumerate(game.entities[1 : game.maxclients + 1], start=1):
        if not e or not e.inuse or not e.client:
            continue
        ping = getattr(e.client, "ping", 0)
        score = getattr(e.client.resp, "score", 0)
        name = e.client.pers.netname
        lines.append(f"{i:2d} {score:3d} {ping:3d} {name}")
    _cprintf(ent, "\n".join(lines) + "\n")


def ClientCommand(ent):
    if not ent or not ent.client:
        return
    cmd = _cmd_argv(0).lower()
    if cmd == "players":
        Cmd_Players_f(ent)
    elif cmd == "say":
        Cmd_Say_f(ent, False, False)
    elif cmd == "say_team":
        Cmd_Say_f(ent, True, False)
    elif cmd == "score":
        ent.client.showscores = True
    elif cmd == "help":
        ent.client.showhelp = True
    elif cmd == "inven":
        Cmd_Inven_f(ent)
    elif cmd == "invuse":
        Cmd_InvUse_f(ent)
    elif cmd == "invdrop":
        Cmd_InvDrop_f(ent)
    elif cmd == "weapprev":
        Cmd_WeapPrev_f(ent)
    elif cmd == "weapnext":
        Cmd_WeapNext_f(ent)
    elif cmd == "weaplast":
        Cmd_WeapLast_f(ent)
    elif cmd == "kill":
        Cmd_Kill_f(ent)
    elif cmd == "putaway":
        Cmd_PutAway_f(ent)
    elif cmd == "god":
        Cmd_God_f(ent)
    elif cmd == "notarget":
        Cmd_Notarget_f(ent)
    elif cmd == "noclip":
        Cmd_Noclip_f(ent)
    elif cmd == "use":
        Cmd_Use_f(ent)
    elif cmd == "drop":
        Cmd_Drop_f(ent)
    elif cmd == "give":
        Cmd_Give_f(ent)
    elif cmd == "playerlist":
        Cmd_PlayerList_f(ent)
    elif cmd == "wave":
        Cmd_Wave_f(ent)
    else:
        Cmd_Say_f(ent, False, True)
