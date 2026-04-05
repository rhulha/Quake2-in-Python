import math
import random

from .reference_import import gi


WEAPON_READY = 0
WEAPON_ACTIVATING = 1
WEAPON_DROPPING = 2
WEAPON_FIRING = 3


def _game():
    from .g_main import game
    return game


def _angles_to_forward(angles):
    pitch = math.radians(angles[0])
    yaw = math.radians(angles[1])
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    return [cp * cy, cp * sy, -sp]


def P_ProjectSource(client, point, distance, forward, right):
    return [
        point[0] + forward[0] * distance[0] + right[0] * distance[1],
        point[1] + forward[1] * distance[0] + right[1] * distance[1],
        point[2] + forward[2] * distance[0] + distance[2],
    ]


def PlayerNoise(who, where, _type):
    if not who or not who.client:
        return
    who.client.last_noise_time = getattr(_game().level, "time", 0.0)
    who.client.last_noise_pos = list(where)
    who.client.last_noise_type = _type


def Pickup_Weapon(ent, other):
    if not other or not other.client or not ent or not ent.item:
        return False
    idx = ent.item.index
    other.client.pers.inventory[idx] += 1
    return True


def ChangeWeapon(ent):
    if not ent or not ent.client:
        return
    client = ent.client
    if not client.newweapon:
        return
    client.pers.lastweapon = client.pers.weapon
    client.pers.weapon = client.newweapon
    client.newweapon = None
    client.weaponstate = WEAPON_ACTIVATING
    client.ps.gunframe = 0


def NoAmmoWeaponChange(ent):
    if not ent or not ent.client:
        return
    client = ent.client
    if client.pers.weapon and client.pers.inventory[client.pers.weapon.index] > 0:
        return
    for item in getattr(_game(), "itemlist", []):
        if not item:
            continue
        if item.flags & 1 and client.pers.inventory[item.index] > 0:
            client.newweapon = item
            return


def Think_Weapon(ent):
    if not ent or not ent.client:
        return
    client = ent.client

    if ent.health <= 0:
        client.newweapon = None
        ChangeWeapon(ent)
        return

    if client.newweapon:
        ChangeWeapon(ent)

    weapon = client.pers.weapon
    if weapon and weapon.weaponthink:
        weapon.weaponthink(ent)


def Use_Weapon(ent, item):
    if not ent or not ent.client or not item:
        return
    if ent.client.pers.weapon is item:
        return
    ent.client.newweapon = item


def Drop_Weapon(ent, item):
    if not ent or not ent.client or not item:
        return
    idx = item.index
    if ent.client.pers.inventory[idx] <= 0:
        return
    ent.client.pers.inventory[idx] -= 1
    try:
        from .g_items import Drop_Item
        Drop_Item(ent, item)
    except Exception:
        return


def Weapon_Generic(ent, FRAME_ACTIVATE_LAST, FRAME_FIRE_LAST, FRAME_IDLE_LAST, FRAME_DEACTIVATE_LAST, pause_frames, fire_frames, fire):
    if not ent or not ent.client:
        return

    client = ent.client
    if client.weaponstate == WEAPON_ACTIVATING:
        client.ps.gunframe += 1
        if client.ps.gunframe >= FRAME_ACTIVATE_LAST:
            client.weaponstate = WEAPON_READY
            client.ps.gunframe = FRAME_FIRE_LAST + 1
        return

    if client.weaponstate == WEAPON_DROPPING:
        client.ps.gunframe += 1
        if client.ps.gunframe >= FRAME_DEACTIVATE_LAST:
            ChangeWeapon(ent)
        return

    if client.weaponstate == WEAPON_FIRING:
        for f in fire_frames:
            if client.ps.gunframe == f:
                fire(ent)
                break
        client.ps.gunframe += 1
        if client.ps.gunframe > FRAME_IDLE_LAST:
            client.weaponstate = WEAPON_READY
            client.ps.gunframe = FRAME_FIRE_LAST + 1
        return

    if client.weaponstate == WEAPON_READY:
        attack_pressed = bool(client.buttons & 1) if hasattr(client, "buttons") else False
        if attack_pressed:
            client.weaponstate = WEAPON_FIRING
            client.ps.gunframe = FRAME_FIRE_LAST
            return

        client.ps.gunframe += 1
        if client.ps.gunframe > FRAME_IDLE_LAST:
            client.ps.gunframe = FRAME_FIRE_LAST + 1
        if pause_frames and client.ps.gunframe in pause_frames and random.randint(0, 15):
            client.ps.gunframe -= 1


def _consume_ammo(ent, count):
    client = ent.client
    w = client.pers.weapon
    if not w or not w.ammo:
        return True
    from .g_items import FindItem
    ammo_item = FindItem(w.ammo)
    if not ammo_item:
        return True
    idx = ammo_item.index
    if client.pers.inventory[idx] < count:
        NoAmmoWeaponChange(ent)
        return False
    client.pers.inventory[idx] -= count
    client.ammo_index = idx
    return True


def _fire_hitscan(ent, damage, kick, hspread=0, vspread=0, shots=1):
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_bullet, fire_shotgun
    if shots == 1:
        fire_bullet(ent, start, forward, damage, kick, hspread, vspread, 0)
    else:
        fire_shotgun(ent, start, forward, damage, kick, hspread, vspread, shots, 0)
    PlayerNoise(ent, start, 0)


def weapon_grenade_fire(ent):
    if not _consume_ammo(ent, 1):
        return
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_grenade2
    fire_grenade2(ent, start, forward, 120, 600, 2.5, 120)
    PlayerNoise(ent, start, 0)


def Weapon_Grenade(ent):
    Weapon_Generic(ent, 16, 5, 48, 52, [34, 51], [5], weapon_grenade_fire)


def weapon_grenadelauncher_fire(ent):
    if not _consume_ammo(ent, 1):
        return
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_grenade
    fire_grenade(ent, start, forward, 120, 600, 2.5, 120)
    PlayerNoise(ent, start, 0)


def Weapon_GrenadeLauncher(ent):
    Weapon_Generic(ent, 5, 6, 59, 64, [34, 51], [6], weapon_grenadelauncher_fire)


def Weapon_RocketLauncher_Fire(ent):
    if not _consume_ammo(ent, 1):
        return
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_rocket
    fire_rocket(ent, start, forward, 100, 650, 120, 120)
    PlayerNoise(ent, start, 0)


def Weapon_RocketLauncher(ent):
    Weapon_Generic(ent, 4, 5, 50, 54, [25, 33, 42, 50], [5], Weapon_RocketLauncher_Fire)


def Blaster_Fire(ent, g_offset, damage, hyper, effect):
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_blaster
    fire_blaster(ent, start, forward, damage, 1000, effect, hyper)
    PlayerNoise(ent, start, 0)


def Weapon_Blaster_Fire(ent):
    Blaster_Fire(ent, [24, 8, ent.viewheight - 8], 15, False, 8)


def Weapon_Blaster(ent):
    Weapon_Generic(ent, 4, 5, 52, 55, [19, 32], [5], Weapon_Blaster_Fire)


def Weapon_HyperBlaster_Fire(ent):
    if not _consume_ammo(ent, 1):
        return
    Blaster_Fire(ent, [24, 8, ent.viewheight - 8], 20, True, 8)


def Weapon_HyperBlaster(ent):
    Weapon_Generic(ent, 5, 6, 49, 53, [0], [6, 7, 8, 9, 10, 11], Weapon_HyperBlaster_Fire)


def Machinegun_Fire(ent):
    if not _consume_ammo(ent, 1):
        return
    _fire_hitscan(ent, 8, 2, 300, 500, 1)


def Weapon_Machinegun(ent):
    Weapon_Generic(ent, 3, 4, 45, 49, [23, 45], [4, 5], Machinegun_Fire)


def Chaingun_Fire(ent):
    if not _consume_ammo(ent, 2):
        return
    _fire_hitscan(ent, 6, 2, 300, 500, 2)


def Weapon_Chaingun(ent):
    Weapon_Generic(ent, 5, 6, 64, 69, [38, 43, 51, 61], [6, 7, 8, 9, 10, 11], Chaingun_Fire)


def weapon_shotgun_fire(ent):
    if not _consume_ammo(ent, 1):
        return
    _fire_hitscan(ent, 4, 8, 500, 500, 12)


def Weapon_Shotgun(ent):
    Weapon_Generic(ent, 7, 8, 36, 39, [22, 28, 34], [8], weapon_shotgun_fire)


def weapon_supershotgun_fire(ent):
    if not _consume_ammo(ent, 2):
        return
    _fire_hitscan(ent, 6, 12, 1000, 500, 20)


def Weapon_SuperShotgun(ent):
    Weapon_Generic(ent, 6, 7, 57, 61, [29, 42, 57], [7], weapon_supershotgun_fire)


def weapon_railgun_fire(ent):
    if not _consume_ammo(ent, 1):
        return
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_rail
    fire_rail(ent, start, forward, 100, 200)
    PlayerNoise(ent, start, 0)


def Weapon_Railgun(ent):
    Weapon_Generic(ent, 4, 5, 61, 64, [56], [5], weapon_railgun_fire)


def weapon_bfg_fire(ent):
    if not _consume_ammo(ent, 50):
        return
    start = list(ent.s.origin)
    start[2] += ent.viewheight if hasattr(ent, "viewheight") else 22
    forward = _angles_to_forward(ent.client.v_angle)
    from .g_weapon import fire_bfg
    fire_bfg(ent, start, forward, 200, 400, 1000)
    PlayerNoise(ent, start, 0)


def Weapon_BFG(ent):
    Weapon_Generic(ent, 8, 9, 64, 69, [39, 45, 50, 55], [9], weapon_bfg_fire)
