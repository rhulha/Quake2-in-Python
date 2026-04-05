from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

MAXMENUITEMS = 64

MTYPE_SLIDER = 0
MTYPE_LIST = 1
MTYPE_ACTION = 2
MTYPE_SPINCONTROL = 3
MTYPE_SEPARATOR = 4
MTYPE_FIELD = 5

QMF_LEFT_JUSTIFY = 0x00000001
QMF_GRAYED = 0x00000002
QMF_NUMBERSONLY = 0x00000004


def _generic(item):
    return item.get('generic', item)


def Action_DoEnter(a):
    g = _generic(a)
    cb = g.get('callback')
    if cb:
        cb(a)


def Action_Draw(a):
    return


def Field_DoEnter(f):
    g = _generic(f)
    cb = g.get('callback')
    if cb:
        cb(f)
        return True
    return False


def Field_Draw(f):
    return


def Field_Key(f, key):
    g = _generic(f)
    buf = g.get('buffer', bytearray())
    cursor = g.get('cursor', 0)
    length = g.get('length', len(buf))
    flags = g.get('flags', 0)

    K_LEFTARROW = 130
    K_BACKSPACE = 127
    K_DEL = 8
    K_ENTER = 13
    K_ESCAPE = 27
    K_TAB = 9

    if key in (K_ENTER, K_ESCAPE, K_TAB):
        return False
    if key == K_BACKSPACE or key == K_LEFTARROW:
        if cursor > 0:
            if isinstance(buf, (bytearray, list)):
                buf.pop(cursor - 1)
            g['cursor'] = cursor - 1
        return True
    if key == K_DEL:
        if cursor < len(buf):
            if isinstance(buf, (bytearray, list)):
                buf.pop(cursor)
        return True
    if key > 127:
        return False
    if (flags & QMF_NUMBERSONLY) and not chr(key).isdigit():
        return False
    if cursor < length:
        if isinstance(buf, bytearray):
            buf.insert(cursor, key)
        g['cursor'] = cursor + 1
    return True


def Menu_AddItem(menu, item):
    if menu.get('nitems', 0) == 0:
        menu['nslots'] = 0
    if menu.get('nitems', 0) < MAXMENUITEMS:
        if 'items' not in menu:
            menu['items'] = []
        menu['items'].append(item)
        _generic(item)['parent'] = menu
        menu['nitems'] = menu.get('nitems', 0) + 1
    menu['nslots'] = Menu_TallySlots(menu)


def Menu_AdjustCursor(m, _dir):
    nitems = m.get('nitems', 0)
    if nitems == 0:
        return
    cursor = m.get('cursor', 0)
    if 0 <= cursor < nitems:
        citem = Menu_ItemAtCursor(m)
        if citem and _generic(citem).get('type') != MTYPE_SEPARATOR:
            return
    if _dir == 1:
        while True:
            citem = Menu_ItemAtCursor(m)
            if citem and _generic(citem).get('type') != MTYPE_SEPARATOR:
                break
            m['cursor'] = m.get('cursor', 0) + _dir
            if m['cursor'] >= nitems:
                m['cursor'] = 0
    else:
        while True:
            citem = Menu_ItemAtCursor(m)
            if citem and _generic(citem).get('type') != MTYPE_SEPARATOR:
                break
            m['cursor'] = m.get('cursor', 0) + _dir
            if m['cursor'] < 0:
                m['cursor'] = nitems - 1


def Menu_Center(menu):
    items = menu.get('items', [])
    if not items:
        return
    height = _generic(items[-1]).get('y', 0) + 10
    menu['y'] = (480 - height) // 2


def Menu_Draw(menu):
    return


def Menu_DrawStatusBar(string):
    return


def Menu_DrawString(x, y, string):
    return


def Menu_DrawStringDark(x, y, string):
    return


def Menu_DrawStringR2L(x, y, string):
    return


def Menu_DrawStringR2LDark(x, y, string):
    return


def Menu_ItemAtCursor(m):
    cursor = m.get('cursor', 0)
    items = m.get('items', [])
    if cursor < 0 or cursor >= len(items):
        return None
    return items[cursor]


def Menu_SelectItem(s):
    item = Menu_ItemAtCursor(s)
    if item:
        t = _generic(item).get('type')
        if t == MTYPE_FIELD:
            return Field_DoEnter(item)
        elif t == MTYPE_ACTION:
            Action_DoEnter(item)
            return True
    return False


def Menu_SetStatusBar(m, string):
    m['statusbar'] = string


def Menu_SlideItem(s, _dir):
    item = Menu_ItemAtCursor(s)
    if item:
        t = _generic(item).get('type')
        if t == MTYPE_SLIDER:
            Slider_DoSlide(item, _dir)
        elif t == MTYPE_SPINCONTROL:
            SpinControl_DoSlide(item, _dir)


def Menu_TallySlots(menu):
    total = 0
    for item in menu.get('items', []):
        g = _generic(item)
        if g.get('type') == MTYPE_LIST:
            names = item.get('itemnames', [])
            total += len([n for n in names if n])
        else:
            total += 1
    return total


def Menulist_DoEnter(l):
    g = _generic(l)
    parent = g.get('parent', {})
    start = g.get('y', 0) // 10 + 1
    l['curvalue'] = parent.get('cursor', 0) - start
    cb = g.get('callback')
    if cb:
        cb(l)


def MenuList_Draw(l):
    return


def Separator_Draw(s):
    return


def Slider_DoSlide(s, _dir):
    s['curvalue'] = s.get('curvalue', 0) + _dir
    if s['curvalue'] > s.get('maxvalue', 1):
        s['curvalue'] = s.get('maxvalue', 1)
    elif s['curvalue'] < s.get('minvalue', 0):
        s['curvalue'] = s.get('minvalue', 0)
    g = _generic(s)
    cb = g.get('callback')
    if cb:
        cb(s)


def Slider_Draw(s):
    return


def SpinControl_DoEnter(s):
    s['curvalue'] = s.get('curvalue', 0) + 1
    names = s.get('itemnames', [])
    if s['curvalue'] >= len(names) or not names[s['curvalue']]:
        s['curvalue'] = 0
    g = _generic(s)
    cb = g.get('callback')
    if cb:
        cb(s)


def SpinControl_DoSlide(s, _dir):
    s['curvalue'] = s.get('curvalue', 0) + _dir
    names = s.get('itemnames', [])
    if s['curvalue'] < 0:
        s['curvalue'] = 0
    elif s['curvalue'] >= len(names) or not names[s['curvalue']]:
        s['curvalue'] = max(0, s['curvalue'] - 1)
    g = _generic(s)
    cb = g.get('callback')
    if cb:
        cb(s)


def SpinControl_Draw(s):
    return
