"""Сверка прогонов бота: кого видел в комнатах и не узнал (нет в _mob.csv маршрута).
python -X utf8 bot_audit.py <лог игры> [зона ...]
Окна зон — по строкам ## BOT_START zone=… / ## ZONE_END в логе. Содержимое комнаты — строки после «[ Exits: …]» до промпта.
Строка считается «знакомой», если совпадает с описанием в _mob.csv (без хвостовых пробелов) или с предметом/трупом/монетами."""
import os, sys, re, collections
AREAS = r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА\areas"
SKIP = re.compile(r"(лежит здесь|лежит тут|валяется|Труп |труп |Кучка монет|Останки|стоит тут\.\.\.|расположен тут|светится|\(летит\)$|^\[Зона)", re.I)


def mobs(zone):
    f = os.path.join(AREAS, zone + "_mob.csv")
    s = set()
    if os.path.exists(f):
        for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
            p = l.split('";"')
            if len(p) > 1: s.add(p[1].strip().strip('"').strip())
    return s


log = open(sys.argv[1], encoding="cp1251", errors="replace").read().splitlines()
want = set(sys.argv[2:])
zone = None; inroom = False; seen = collections.defaultdict(collections.Counter); known = {}
for l in log:
    t = l[9:] if re.match(r"\d\d:\d\d:\d\d ", l) else l
    m = re.search(r"## BOT_START zone=(\S+)", t)
    if m:
        zone = m.group(1); known.setdefault(zone, mobs(zone)); continue
    if "## ZONE_END" in t or "## BOT_STOP" in t:
        zone = None; continue
    if not zone or (want and zone not in want): continue
    if t.startswith("[ Exits:"): inroom = True; continue
    if re.search(r"\d+H \d+M \d+V", t) or t.startswith("##") or t.startswith(">>"): inroom = False; continue
    if inroom and t.strip() and not t.startswith("   ") and not SKIP.search(t):
        if t.strip() not in known[zone]:
            seen[zone][t.strip()] += 1
for z in seen:
    print("=== %s (в _mob.csv %d)" % (z, len(known[z])))
    for line, n in seen[z].most_common(12):
        print("  %3d  %s" % (n, line[:100]))
