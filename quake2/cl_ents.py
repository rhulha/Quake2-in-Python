"""
cl_ents.py - Entity management for client rendering
Handles entity updates, interpolation, and scene assembly
"""

from shared.render_types import entity_t


def CL_ParseEntityBits(bits):
    """Parse entity update bits"""
    pass


def CL_ParseDelta(_from, _to, number, bits):
    """Apply delta-compressed entity update"""
    pass


def CL_DeltaEntity(frame, newnum, old, bits):
    """Process delta entity update"""
    pass


def CL_ParsePacketEntities(oldframe, newframe):
    """Parse entity updates from server packet"""
    pass


def CL_ParsePlayerstate(oldframe, newframe):
    """Parse player state from server"""
    pass


def CL_FireEntityEvents(frame):
    """Fire entity event functions"""
    pass


def CL_ParseFrame():
    """Parse server frame"""
    pass


def CL_AddPacketEntities(frame):
    """Add entities from packet to render list"""
    pass


def CL_AddViewWeapon(os, ops):
    """Add weapon view model"""
    pass


def CL_CalcViewValues():
    """Calculate view position and angles"""
    pass


def CL_AddEntities():
    """Add all entities to render scene from server state"""
    try:
        from . import sv_main
        from . import cl_view

        if not sv_main.server or not sv_main.server.edicts:
            return

        # Clear scene
        cl_view.V_ClearScene()

        # Add entities from server
        for idx, edict in enumerate(sv_main.server.edicts):
            if edict is None:
                continue

            # Skip player entity (entity 0)
            if idx == 0:
                continue

            # Create entity_t
            ent = entity_t(
                model=edict.model if hasattr(edict, 'model') else None,
                origin=list(edict.origin) if hasattr(edict, 'origin') else [0, 0, 0],
                angles=list(edict.angles) if hasattr(edict, 'angles') else [0, 0, 0],
                frame=int(edict.frame) if hasattr(edict, 'frame') else 0,
                oldorigin=list(edict.oldorigin) if hasattr(edict, 'oldorigin') else [0, 0, 0],
                oldframe=int(edict.oldframe) if hasattr(edict, 'oldframe') else 0,
                backlerp=float(edict.backlerp) if hasattr(edict, 'backlerp') else 0.0,
                skinnum=int(edict.skinnum) if hasattr(edict, 'skinnum') else 0,
                lightstyle=int(edict.lightstyle) if hasattr(edict, 'lightstyle') else 0,
                alpha=float(edict.alpha) if hasattr(edict, 'alpha') else 1.0,
                skin=edict.skin if hasattr(edict, 'skin') else None,
                flags=int(edict.flags) if hasattr(edict, 'flags') else 0,
            )

            cl_view.V_AddEntity(ent)

    except Exception as e:
        print(f"CL_AddEntities error: {e}")


def CL_GetEntitySoundOrigin(entity_num):
    """Get sound origin for entity"""
    try:
        from . import sv_main

        if sv_main.server and sv_main.server.edicts:
            if 0 <= entity_num < len(sv_main.server.edicts):
                edict = sv_main.server.edicts[entity_num]
                if edict and hasattr(edict, 'origin'):
                    return edict.origin

    except:
        pass

    return [0, 0, 0]

