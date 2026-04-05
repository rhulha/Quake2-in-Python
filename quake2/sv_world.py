from dataclasses import dataclass, field

from .sv_main import server
from .cmodel import (
    CTrace,
    CM_BoxTrace,
    CM_HeadnodeForBox,
    CM_PointContents,
    CM_TransformedPointContents,
    CM_TransformedBoxTrace,
)
from shared.QEnums import solid_t


AREA_DEPTH = 4
AREA_NODES = 32
AREA_SOLID = 1
AREA_TRIGGER = 2
MAX_TOTAL_ENT_LEAFS = 128


@dataclass
class link_t:
    prev: object = None
    next: object = None
    owner: object = None


@dataclass
class areanode_t:
    axis: int = -1
    dist: float = 0.0
    children: list = field(default_factory=lambda: [None, None])
    trigger_edicts: link_t = field(default_factory=link_t)
    solid_edicts: link_t = field(default_factory=link_t)


@dataclass
class moveclip_t:
    boxmins: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    boxmaxs: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    mins: list = None
    maxs: list = None
    mins2: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    maxs2: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    start: list = None
    end: list = None
    trace: object = None
    passedict: object = None
    contentmask: int = 0


sv_areanodes = []
sv_numareanodes = 0

area_mins = [0.0, 0.0, 0.0]
area_maxs = [0.0, 0.0, 0.0]
area_list = []
area_count = 0
area_maxcount = 0
area_type = AREA_SOLID


def _ent_from_link(l):
    return l.owner


def ClearLink(l):
    l.prev = l
    l.next = l


def RemoveLink(l):
    l.next.prev = l.prev
    l.prev.next = l.next
    l.prev = None
    l.next = None


def InsertLinkBefore(l, before):
    l.next = before
    l.prev = before.prev
    l.prev.next = l
    l.next.prev = l


def SV_CreateAreaNode(depth, mins, maxs):
    global sv_numareanodes
    if sv_numareanodes >= AREA_NODES:
        return None

    anode = sv_areanodes[sv_numareanodes]
    sv_numareanodes += 1

    ClearLink(anode.trigger_edicts)
    ClearLink(anode.solid_edicts)

    if depth == AREA_DEPTH:
        anode.axis = -1
        anode.children = [None, None]
        return anode

    size = [maxs[i] - mins[i] for i in range(3)]
    anode.axis = 0 if size[0] > size[1] else 1
    anode.dist = 0.5 * (maxs[anode.axis] + mins[anode.axis])

    mins1 = list(mins)
    mins2 = list(mins)
    maxs1 = list(maxs)
    maxs2 = list(maxs)
    maxs1[anode.axis] = anode.dist
    mins2[anode.axis] = anode.dist

    anode.children[0] = SV_CreateAreaNode(depth + 1, mins2, maxs2)
    anode.children[1] = SV_CreateAreaNode(depth + 1, mins1, maxs1)
    return anode


def SV_ClearWorld():
    global sv_areanodes, sv_numareanodes
    sv_areanodes = [areanode_t() for _ in range(AREA_NODES)]
    for n in sv_areanodes:
        n.trigger_edicts.owner = None
        n.solid_edicts.owner = None
    sv_numareanodes = 0

    mins = [-4096.0, -4096.0, -4096.0]
    maxs = [4096.0, 4096.0, 4096.0]
    if getattr(server, "models", None) and len(server.models) > 1 and server.models[1]:
        model = server.models[1]
        if hasattr(model, "mins") and hasattr(model, "maxs"):
            mins = list(model.mins)
            maxs = list(model.maxs)

    SV_CreateAreaNode(0, mins, maxs)


def SV_UnlinkEdict(ent):
    if not getattr(ent, "area", None):
        return
    if not getattr(ent.area, "prev", None):
        return
    RemoveLink(ent.area)


def SV_LinkEdict(ent):
    if getattr(ent, "area", None) and getattr(ent.area, "prev", None):
        SV_UnlinkEdict(ent)

    if not ent or not getattr(ent, "inuse", False):
        return

    if not getattr(ent, "area", None):
        ent.area = link_t(owner=ent)
    elif getattr(ent.area, "owner", None) is None:
        ent.area.owner = ent

    for i in range(3):
        ent.size[i] = ent.maxs[i] - ent.mins[i]

    if ent.solid == solid_t.SOLID_BBOX and not (ent.svflags & 0x00000020):
        i = int(ent.maxs[0] / 8)
        i = 1 if i < 1 else (31 if i > 31 else i)
        j = int((-ent.mins[2]) / 8)
        j = 1 if j < 1 else (31 if j > 31 else j)
        k = int((ent.maxs[2] + 32) / 8)
        k = 1 if k < 1 else (63 if k > 63 else k)
        ent.s.solid = (k << 10) | (j << 5) | i
    elif ent.solid == solid_t.SOLID_BSP:
        ent.s.solid = 31
    else:
        ent.s.solid = 0

    if ent.solid == solid_t.SOLID_BSP and (ent.s.angles[0] or ent.s.angles[1] or ent.s.angles[2]):
        max_v = 0.0
        for i in range(3):
            max_v = max(max_v, abs(ent.mins[i]), abs(ent.maxs[i]))
        for i in range(3):
            ent.absmin[i] = ent.s.origin[i] - max_v
            ent.absmax[i] = ent.s.origin[i] + max_v
    else:
        for i in range(3):
            ent.absmin[i] = ent.s.origin[i] + ent.mins[i]
            ent.absmax[i] = ent.s.origin[i] + ent.maxs[i]

    for i in range(3):
        ent.absmin[i] -= 1
        ent.absmax[i] += 1

    if not getattr(ent, "linkcount", 0):
        ent.s.old_origin[:] = list(ent.s.origin)
    ent.linkcount += 1

    if ent.solid == solid_t.SOLID_NOT:
        return

    node = sv_areanodes[0] if sv_areanodes else None
    while node:
        if node.axis == -1:
            break
        if ent.absmin[node.axis] > node.dist:
            node = node.children[0]
        elif ent.absmax[node.axis] < node.dist:
            node = node.children[1]
        else:
            break

    if not node:
        return
    if ent.solid == solid_t.SOLID_TRIGGER:
        InsertLinkBefore(ent.area, node.trigger_edicts)
    else:
        InsertLinkBefore(ent.area, node.solid_edicts)


def SV_AreaEdicts_r(node):
    global area_count
    start = node.solid_edicts if area_type == AREA_SOLID else node.trigger_edicts
    l = start.next
    while l is not None and l is not start:
        nxt = l.next
        check = _ent_from_link(l)
        if check and check.solid != solid_t.SOLID_NOT:
            if not (
                check.absmin[0] > area_maxs[0]
                or check.absmin[1] > area_maxs[1]
                or check.absmin[2] > area_maxs[2]
                or check.absmax[0] < area_mins[0]
                or check.absmax[1] < area_mins[1]
                or check.absmax[2] < area_mins[2]
            ):
                if area_count == area_maxcount:
                    return
                area_list[area_count] = check
                area_count += 1
        l = nxt

    if node.axis == -1:
        return
    if area_maxs[node.axis] > node.dist and node.children[0]:
        SV_AreaEdicts_r(node.children[0])
    if area_mins[node.axis] < node.dist and node.children[1]:
        SV_AreaEdicts_r(node.children[1])


def SV_AreaEdicts(mins, maxs, _list, maxcount, areatype):
    global area_mins, area_maxs, area_list, area_count, area_maxcount, area_type
    area_mins = mins
    area_maxs = maxs
    area_list = _list
    area_count = 0
    area_maxcount = maxcount
    area_type = areatype
    if sv_areanodes:
        SV_AreaEdicts_r(sv_areanodes[0])
    return area_count


def SV_PointContents(p):
    contents = CM_PointContents(p, 0)
    touch = [None] * max(1, len(server.edicts) if getattr(server, "edicts", None) else 1024)
    num = SV_AreaEdicts(p, p, touch, len(touch), AREA_SOLID)
    for i in range(num):
        hit = touch[i]
        headnode = SV_HullForEntity(hit)
        angles = hit.s.angles if hit.solid == solid_t.SOLID_BSP else [0.0, 0.0, 0.0]
        c2 = CM_TransformedPointContents(p, headnode, hit.s.origin, angles)
        contents |= c2
    return contents


def SV_HullForEntity(ent):
    if ent.solid == solid_t.SOLID_BSP:
        model_index = getattr(ent.s, "modelindex", 0)
        if getattr(server, "models", None) and 0 <= model_index < len(server.models):
            model = server.models[model_index]
            if hasattr(model, "headnode"):
                return model.headnode
        return 0
    return CM_HeadnodeForBox(ent.mins, ent.maxs)


def SV_ClipMoveToEntities(clip):
    touchlist = [None] * max(1, len(server.edicts) if getattr(server, "edicts", None) else 1024)
    num = SV_AreaEdicts(clip.boxmins, clip.boxmaxs, touchlist, len(touchlist), AREA_SOLID)
    for i in range(num):
        touch = touchlist[i]
        if not touch or touch.solid == solid_t.SOLID_NOT:
            continue
        if touch is clip.passedict:
            continue
        if clip.trace.allsolid:
            return
        if clip.passedict:
            if touch.owner is clip.passedict:
                continue
            if getattr(clip.passedict, "owner", None) is touch:
                continue

        headnode = SV_HullForEntity(touch)
        angles = touch.s.angles if touch.solid == solid_t.SOLID_BSP else [0.0, 0.0, 0.0]
        is_monster = bool(touch.svflags & 0x00000001)

        if is_monster:
            trace = CM_TransformedBoxTrace(
                clip.start,
                clip.end,
                clip.mins2,
                clip.maxs2,
                headnode,
                clip.contentmask,
                touch.s.origin,
                angles,
            )
        else:
            trace = CM_TransformedBoxTrace(
                clip.start,
                clip.end,
                clip.mins,
                clip.maxs,
                headnode,
                clip.contentmask,
                touch.s.origin,
                angles,
            )

        if trace.allsolid or trace.startsolid or trace.fraction < clip.trace.fraction:
            trace.ent = touch
            if clip.trace.startsolid:
                clip.trace = trace
                clip.trace.startsolid = True
            else:
                clip.trace = trace
        elif trace.startsolid:
            clip.trace.startsolid = True


def SV_TraceBounds(start, mins, maxs, end, boxmins, boxmaxs):
    for i in range(3):
        if end[i] > start[i]:
            boxmins[i] = start[i] + mins[i] - 1
            boxmaxs[i] = end[i] + maxs[i] + 1
        else:
            boxmins[i] = end[i] + mins[i] - 1
            boxmaxs[i] = start[i] + maxs[i] + 1


def SV_Trace(start, mins, maxs, end, passedict, contentmask):
    if mins is None:
        mins = [0.0, 0.0, 0.0]
    if maxs is None:
        maxs = [0.0, 0.0, 0.0]

    clip = moveclip_t()
    clip.trace = CM_BoxTrace(start, end, mins, maxs, 0, contentmask)
    clip.trace.ent = server.edicts[0] if getattr(server, "edicts", None) else None
    if clip.trace.fraction == 0:
        return clip.trace

    clip.contentmask = contentmask
    clip.start = start
    clip.end = end
    clip.mins = mins
    clip.maxs = maxs
    clip.passedict = passedict
    clip.mins2[:] = list(mins)
    clip.maxs2[:] = list(maxs)

    SV_TraceBounds(start, clip.mins2, clip.maxs2, end, clip.boxmins, clip.boxmaxs)
    SV_ClipMoveToEntities(clip)
    return clip.trace
