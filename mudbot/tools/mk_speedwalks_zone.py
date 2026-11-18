# -*- coding: utf-8 -*-
"""Спидволки в маршрутах зон Айлины (слова пользователя 13.11: переходы - пачкой команд через ';', в пути не драться).
Для каждой зоны: переход «склад -> зона» (до создания области / до первой клетки зоны) и «зона -> склад» (после последней клетки зоны) сжимается:
подряд идущие V-строки с чистыми ходами -> одна V-строка в первой клетке с командами через ';' (не больше 14). После последней клетки зоны ставится
.триг #scr botCore.BotInZone = false. Двери/команды не трогаю. Бэкап .bak_swalk. python tools/mk_speedwalks_zone.py <зона>=<префикс vnum зоны> ..."""
import os, re, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
AREAS = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
RUNMAX = int(os.environ.get("RUNMAX", "40"))     # длина пачки ходов: 1 = одиночные шаги с проверкой клетки (пачки обрываются очисткой очереди)
SWAMP = "111"            # болото: пиявки агро, пачка прерывается - тут одиночные шаги с проверкой клетки (слова пользователя 13.11)
DIRS = {"север", "юг", "запад", "восток", "вверх", "вниз"}
V = re.compile(r"^#if \{\$MsdpRoomVnum != (\d+)\} \{[^}]*\};#if \{\$MsdpRoomVnum == \1\} \{([^}]*)\}\s*$")
HEAD = "#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}"
OFF = ".триг #scr botCore.BotInZone = false"


def compress(seg):
    out = []; run = []
    def flush():
        if run:
            cmds = ";".join(c for _, c in run)
            if len(run) > 1:
                cmds += ";#scr botCore.wait(%d)" % (len(run) * 3 + 10)      # бот на время пачки не шагает: иначе mismatch-ветка следующей строки делает очистить и стирает остаток
            out.append(HEAD % (run[0][0], run[0][0], cmds))
    for ln in seg:
        m = V.match(ln.strip())
        if m and m.group(2).strip() in DIRS and not m.group(1).startswith(SWAMP):
            run.append((m.group(1), m.group(2).strip()))
            if len(run) >= RUNMAX:
                flush(); run.clear()
        else:
            flush(); run.clear(); out.append(ln)
    flush()
    return out


POINTS = {}
for arg in sys.argv[1:]:
    zone, pref = arg.split("=")
    p = os.path.join(AREAS, zone + ".botp")
    L = [x for x in open(p, "rb").read().decode("cp1251").splitlines()]
    while L and not L[-1].strip():
        L.pop()
    idx = [i for i, s in enumerate(L) if (V.match(s.strip()) and V.match(s.strip()).group(1).startswith(pref))]
    if not idx:
        print(zone, ": клеток зоны с префиксом", pref, "нет - пропуск"); continue
    first, last = idx[0], idx[-1]
    entry = first
    for i, s in enumerate(L[:first]):
        if s.startswith(".триг обл с"):
            entry = i; break
    pre = L[:entry]; mid = L[entry:last + 1]; post = L[last + 1:]
    post = [s for s in post if s.strip() != OFF]
    # Б -> А = зеркало пути А -> Б (слова пользователя 13.11): ходы прямого перехода в обратном порядке с противоположными направлениями
    OPP = {"север": "юг", "юг": "север", "запад": "восток", "восток": "запад", "вверх": "вниз", "вниз": "вверх"}
    fw = []; a_vn = None; other = False
    for s in pre:
        m = V.match(s.strip())
        if m and m.group(2).strip() in DIRS:
            if a_vn is None:
                a_vn = m.group(1)
            fw.append(m.group(2).strip())
        elif s.strip() and s.strip() != OFF and not s.startswith(".триг обл с"):
            other = True                       # в переходе есть двери/команды - зеркало не строю, оставляю записанный обратный путь
    mirror = None
    if fw and a_vn and not other:
        import sqlite3, json
        cdb = sqlite3.connect(os.path.join(ROOT, "data", "game.db")); G = {}
        for v, e in cdb.execute("select vnum,exits from rooms"):
            try:
                G[str(v)] = {d: str(t) for d, t in json.loads(e or "{}").items()}
            except Exception:
                G[str(v)] = {}
        L2D = {"север": "N", "юг": "S", "запад": "W", "восток": "E", "вверх": "U", "вниз": "D"}
        cur = a_vn; rooms = [cur]; ok = True
        for d in fw:
            nx = G.get(cur, {}).get(L2D[d])
            if not nx:
                ok = False; break
            cur = nx; rooms.append(cur)
        if ok:
            rev = [OPP[d] for d in reversed(fw)]; rrooms = list(reversed(rooms))[:-1]      # клетки, из которых идёт каждый обратный ход
            mirror = compress([HEAD % (rrooms[i], rrooms[i], rev[i]) for i in range(len(rev))])
            print("   %s: зеркало Б->А построено (%d ходов, Б=%s, А=%s)" % (zone, len(rev), rooms[-1], rooms[0]))
            POINTS[zone] = {"A": rooms[0], "B": rooms[-1]}
        else:
            print("   %s: в графе нет ребра на ходу %d - оставляю записанный обратный путь" % (zone, len(rooms)))
    new = compress(pre) + mid + [OFF] + (mirror if mirror is not None else compress(post)) + [OFF]
    shutil.copy(p, p + ".bak_swalk")
    if zone in POINTS and os.environ.get("USE_WALKER") == "1":
        # слова пользователя 13.11: А (склад) -> Б (вход в зону) спидволком, круг по зоне, возврат в Б, Б -> А. Переходы ведёт ходок надсмотрщика (tools/walker.py),
        # в файле зоны остаётся только круг от клетки Б (создание области) до выхода обратно в Б.
        open(p[:-5] + "_полный.botp", "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251", "replace"))
        new = [OFF] + mid + [OFF]
    open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251", "replace"))
    print("%-10s строк %d -> %d (переход туда: %d -> %d, обратно: %d -> %d)" % (zone, len(L), len(new), len(pre), len(compress(pre)), len(post), len(compress(post))))
import json as _j
_pp = os.path.join(ROOT, "data", "zone_points.json")
_old = _j.load(open(_pp, encoding="utf-8")) if os.path.exists(_pp) else {}
_old.update(POINTS); _j.dump(_old, open(_pp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("точки А/Б:", POINTS)
