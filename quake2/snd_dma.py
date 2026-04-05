from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

_sound_names = {}


def S_SoundInfo_f():
    return


def S_Init():
    return


def S_Shutdown():
    return


def S_FindName(name=''):
    if name in _sound_names:
        return _sound_names[name]
    sfx = {'name': name, 'truename': name, 'registration_sequence': 0}
    _sound_names[name] = sfx
    return sfx


def S_AliasName(aliasname, truename):
    sfx = S_FindName(aliasname)
    sfx['truename'] = truename
    return sfx


def S_BeginRegistration():
    return


def S_RegisterSound(name):
    return S_FindName(name)


def S_EndRegistration():
    return


def S_PickChannel(entnum, entchannel):
    return {'entnum': entnum, 'entchannel': entchannel, 'sfx': None,
            'leftvol': 0, 'rightvol': 0, 'end': 0}


def S_SpatializeOrigin(origin, master_vol, dist_mult, left_vol, right_vol):
    return


def S_Spatialize(ch):
    return


def S_AllocPlaysound():
    return {'sfx': None, 'origin': [0.0, 0.0, 0.0], 'volume': 0.0,
            'attenuation': 0.0, 'entnum': 0, 'entchannel': 0,
            'fixed_origin': False, 'begin': 0}


def S_FreePlaysound(ps):
    return


def S_IssuePlaysound(ps):
    return


def S_RegisterSexedSound(ent, base):
    return S_FindName(base)


def S_StartSound(origin, entnum, entchannel, sfx, fvol, attenuation, timeofs):
    return


def S_StartLocalSound(sound):
    return


def S_ClearBuffer():
    return


def S_StopAllSounds():
    return


def S_AddLoopSounds():
    return


def S_RawSamples(samples, rate, width, channels, data):
    return


def S_Update(origin, forward, right, up):
    return


def GetSoundtime():
    return 0


def S_Update_():
    return


def S_Play():
    return


def S_SoundList():
    return
