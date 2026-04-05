class cplane_t:
    def __init__(self):
        self.normal = [0, 0, 0]
        self.dist = 0
        self.type = 0
        self.signbits = 0
        self.pad = [0, 0]


class sizebuf_t:
    def __init__(self):
        self.allowoverflow = False
        self.overflowed = False
        self.data = None
        self.maxsize = 0
        self.cursize = 0
        self.readcount = 0


class level_locals_t:
    def __init__(self):
        self.framenum = 0
        self.time = 0
        self.levelname = ""
        self.mapname = ""
        self.nextmap = ""
        self.intermissiontime = 0
        self.changemap = ""
        self.exitintermission = 0
        self.intermission_origin = [0, 0, 0]
        self.intermission_angle = [0, 0, 0]

        self.sight_client = None
        self.sight_entity = None
        self.sight_entity_framenum = 0
        self.sound_entity = None
        self.sound_entity_framenum = 0
        self.sound2_entity = None
        self.sound2_entity_framenum = 0

        self.pic_health = 0

        self.total_secrets = 0
        self.found_secrets = 0

        self.total_goals = 0
        self.found_goals = 0

        self.total_monsters = 0
        self.killed_monsters = 0

        self.current_entity = None
        self.body_que = 0
        self.power_cubes = 0


class mmove_t:
    def __init__(self, firstframe, lastframe, frame, endfunc):
        self.firstframe = firstframe
        self.lastframe = lastframe
        self.frame = frame
        self.endfunc = endfunc


class mframe_t:
    def __init__(self, aifunc, dist, thinkfunc):
        self.aifunc = aifunc
        self.dist = dist
        self.thinkfunc = thinkfunc


class monsterinfo_t:
    def __init__(self):
        self.currentmove = None
        self.aiflags = 0
        self.nextframe = 0
        self.scale = 0
        self.stand = None
        self.idle = None
        self.search = None
        self.walk = None
        self.run = None
        self.dodge = None
        self.attack = None
        self.melee = None
        self.sight = None
        self.checkattack = None
        self.pausetime = 0
        self.attack_finished = 0
        self.saved_goal = [0, 0, 0]
        self.search_time = 0
        self.trail_time = 0
        self.last_sighting = [0, 0, 0]
        self.attack_state = 0
        self.lefty = 0
        self.idle_time = 0
        self.linkcount = 0
        self.power_armor_type = 0
        self.power_armor_power = 0


class entity_state_t:
    """Network-visible state of an entity."""
    def __init__(self):
        self.number = 0
        self.origin = [0.0, 0.0, 0.0]
        self.angles = [0.0, 0.0, 0.0]
        self.old_origin = [0.0, 0.0, 0.0]
        self.modelindex = 0
        self.modelindex2 = 0
        self.modelindex3 = 0
        self.modelindex4 = 0
        self.frame = 0
        self.skinnum = 0
        self.effects = 0
        self.renderfx = 0
        self.solid = 0
        self.sound = 0
        self.event = 0


class gclient_persistant_t:
    """Client data that persists across level changes."""
    def __init__(self):
        self.userinfo = ""
        self.netname = ""
        self.hand = 0
        self.connected = False
        self.health = 0
        self.max_health = 0
        self.savedFlags = 0
        self.selected_item = 0
        self.inventory = [0] * 256
        self.max_bullets = 0
        self.max_shells = 0
        self.max_rockets = 0
        self.max_grenades = 0
        self.max_cells = 0
        self.max_slugs = 0
        self.weapon = None
        self.lastweapon = None
        self.power_cubes = 0
        self.score = 0
        self.game_helpchanged = 0
        self.helpchanged = 0
        self.spectator = False


class gclient_respawn_t:
    def __init__(self):
        self.coop_respawn = None
        self.enterframe = 0
        self.score = 0
        self.cmd_angles = [0.0, 0.0, 0.0]
        self.spectator = False


class pmove_state_t:
    def __init__(self):
        self.pm_type = 0
        self.origin = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.pm_flags = 0
        self.pm_time = 0
        self.gravity = 0
        self.delta_angles = [0, 0, 0]


class player_state_t:
    def __init__(self):
        self.pmove = pmove_state_t()
        self.viewangles = [0.0, 0.0, 0.0]
        self.viewoffset = [0.0, 0.0, 0.0]
        self.kick_angles = [0.0, 0.0, 0.0]
        self.gunangles = [0.0, 0.0, 0.0]
        self.gunoffset = [0.0, 0.0, 0.0]
        self.gunindex = 0
        self.gunframe = 0
        self.blend = [0.0, 0.0, 0.0, 0.0]
        self.fov = 90.0
        self.rdflags = 0
        self.stats = [0] * 32


class gclient_t:
    """Per-player game state."""
    def __init__(self):
        self.ps = player_state_t()
        self.ping = 0
        self.pers = gclient_persistant_t()
        self.resp = gclient_respawn_t()
        self.old_pmove = pmove_state_t()
        self.showscores = False
        self.showinventory = False
        self.showhelp = False
        self.showhelpicon = False
        self.ammo_index = 0
        self.buttons = 0
        self.oldbuttons = 0
        self.latched_buttons = 0
        self.weapon_thunk = False
        self.newweapon = None
        self.damage_armor = 0
        self.damage_parmor = 0
        self.damage_blood = 0
        self.damage_knockback = 0
        self.damage_from = [0.0, 0.0, 0.0]
        self.killer_yaw = 0.0
        self.weaponstate = 0
        self.kick_angles = [0.0, 0.0, 0.0]
        self.kick_origin = [0.0, 0.0, 0.0]
        self.v_dmg_roll = 0.0
        self.v_dmg_pitch = 0.0
        self.v_dmg_time = 0.0
        self.fall_time = 0.0
        self.fall_value = 0.0
        self.damage_alpha = 0.0
        self.bonus_alpha = 0.0
        self.damage_blend = [0.0, 0.0, 0.0]
        self.v_angle = [0.0, 0.0, 0.0]
        self.bobtime = 0.0
        self.oldviewangles = [0.0, 0.0, 0.0]
        self.oldvelocity = [0.0, 0.0, 0.0]
        self.next_drown = 0.0
        self.old_waterlevel = 0
        self.breather_sound = 0
        self.machinegun_shots = 0
        self.anim_end = 0
        self.anim_priority = 0
        self.anim_duck = False
        self.anim_run = False
        self.quad_framenum = 0
        self.invincible_framenum = 0
        self.breather_framenum = 0
        self.enviro_framenum = 0
        self.grenade_blew_up = False
        self.grenade_time = 0.0
        self.silencer_shots = 0
        self.weapon_sound = 0
        self.pickup_msg_time = 0.0
        self.flood_locktill = 0.0
        self.flood_when = [0.0] * 10
        self.flood_whenhead = 0
        self.respawn_time = 0.0
        self.chase_target = None
        self.update_chase = False


class gitem_t:
    """Game item definition (weapons, ammo, health, etc.)."""
    def __init__(self):
        self.classname = ""
        self.pickup = None
        self.use = None
        self.drop = None
        self.weaponthink = None
        self.pickup_sound = ""
        self.world_model = ""
        self.world_model_flags = 0
        self.view_model = ""
        self.icon = ""
        self.pickup_name = ""
        self.count_width = 0
        self.quantity = 0
        self.ammo = ""
        self.flags = 0
        self.weapmodel = 0
        self.info = None
        self.tag = 0
        self.precaches = ""
        self.index = 0


class edict_t:
    """Quake 2 entity (edict). Mirrors the C edict_t struct."""

    def __init__(self):
        self.s = entity_state_t()
        self.client = None          # gclient_t, only for players
        self.inuse = False
        self.linkcount = 0

        # Area linking
        self.area = None
        self.num_clusters = 0
        self.clusternums = []
        self.headnode = -1
        self.areanum = 0
        self.areanum2 = 0

        # Server flags / bounding box
        self.svflags = 0
        self.mins = [0.0, 0.0, 0.0]
        self.maxs = [0.0, 0.0, 0.0]
        self.absmin = [0.0, 0.0, 0.0]
        self.absmax = [0.0, 0.0, 0.0]
        self.size = [0.0, 0.0, 0.0]
        self.solid = 0              # solid_t
        self.clipmask = 0
        self.owner = None           # edict_t*

        # Physics
        self.movetype = 0           # movetype_t
        self.flags = 0
        self.model = ""
        self.freetime = 0.0
        self.message = ""
        self.classname = ""
        self.spawnflags = 0
        self.timestamp = 0.0
        self.angle = 0.0
        self.target = ""
        self.targetname = ""
        self.killtarget = ""
        self.team = ""
        self.pathtarget = ""
        self.deathtarget = ""
        self.combattarget = ""
        self.target_ent = None      # edict_t*
        self.speed = 0.0
        self.accel = 0.0
        self.decel = 0.0
        self.movedir = [0.0, 0.0, 0.0]
        self.pos1 = [0.0, 0.0, 0.0]
        self.pos2 = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.avelocity = [0.0, 0.0, 0.0]
        self.mass = 0
        self.air_finished = 0.0
        self.gravity = 1.0
        self.goalentity = None      # edict_t*
        self.movetarget = None      # edict_t*
        self.yaw_speed = 0.0
        self.ideal_yaw = 0.0
        self.nextthink = 0.0
        self.prethink = None
        self.think = None
        self.blocked = None
        self.touch = None
        self.use = None
        self.pain = None
        self.die = None
        self.touch_debounce_time = 0.0
        self.pain_debounce_time = 0.0
        self.damage_debounce_time = 0.0
        self.fly_sound_debounce_time = 0.0
        self.last_move_time = 0.0

        # Combat
        self.health = 0
        self.max_health = 0
        self.gib_health = 0
        self.deadflag = 0
        self.show_hostile = False
        self.powerarmor_time = 0.0
        self.map = ""
        self.viewheight = 0
        self.takedamage = 0         # damage_t
        self.dmg = 0
        self.radius_dmg = 0
        self.dmg_radius = 0.0
        self.sounds = 0
        self.count = 0

        # Entity links
        self.chain = None
        self.enemy = None
        self.oldenemy = None
        self.activator = None
        self.groundentity = None
        self.groundentity_linkcount = 0
        self.teamchain = None
        self.teammaster = None
        self.mynoise = None
        self.mynoise2 = None
        self.noise_index = 0
        self.noise_index2 = 0
        self.volume = 0.0
        self.attenuation = 0.0
        self.wait = 0.0
        self.delay = 0.0
        self.random = 0.0
        self.teleport_time = 0.0
        self.watertype = 0
        self.waterlevel = 0
        self.move_origin = [0.0, 0.0, 0.0]
        self.move_angles = [0.0, 0.0, 0.0]
        self.style = 0
        self.item = None            # gitem_t*
        self.monsterinfo = monsterinfo_t()
        self.index = 0              # entity number in array



