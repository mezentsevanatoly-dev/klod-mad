"""Проверка старого маршрута бота (.botp, шаги направлениями) по карте клеток с номерами + маршрут с номерами клеток.

python -X utf8 route_check.py <файл.botp> [старт=100001] [--write <выход.botp>]
python -X utf8 route_check.py --all <папка> [старт=100001]   -> сводка по всем маршрутам папки

Граф: ЗОНЫ\\*\\клетки.csv (эксплор, номер;название;выходы) + mudbot\\data\\game.db (rooms: vnum, zone, name, exits).
Шаг из известной клетки по выходу -> следующая клетка. Нет такого выхода -> «ошибка шага».
.триг с переездом (ехать, войти, плыть, путь, телепорт, портал…) -> «потерялась»: место ищется заново по следующим шагам
(клетка, из которой следующие шаги все проходят; одна такая — нашлась).
Выход --write: шаг из известной клетки пишется как в маршрутах Айлины:
  #if {$MsdpRoomVnum != N} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == N} {шаг}
остальное (.триг, шаги из неизвестной клетки) — как было."""
import os, sys, re, json, sqlite3, glob

ROOT = r"C:\Users\User\Desktop\Клод мад"
DIRW = {"север": "N", "юг": "S", "запад": "W", "восток": "E", "вверх": "U", "вниз": "D",
        "с": "N", "ю": "S", "з": "W", "в": "E", "вв": "U", "вн": "D", "сев": "N", "зап": "W", "вос": "E", "вост": "E",
        "n": "N", "s": "S", "w": "W", "e": "E", "u": "U", "d": "D"}
WORD = {"N": "север", "S": "юг", "W": "запад", "E": "восток", "U": "вверх", "D": "вниз"}
MOVE_TRIG = re.compile(r"(^|;)\s*(ехать|войти|войт|плыть|путь|телепорт|вход|прыгнуть|залезть|спуститься|подняться|нырнуть|перелезть|переплыть|возврат|recall|подкр)", re.I)


def graph():
    G, names, zones = {}, {}, {}
    db = os.path.join(ROOT, "mudbot", "data", "game.db")
    if os.path.exists(db):
        c = sqlite3.connect(db)
        for v, z, n, ex in c.execute("select vnum, zone, name, exits from rooms"):
            v = str(v)
            try: e = json.loads(ex or "{}")
            except Exception: e = {}
            G.setdefault(v, {}).update({k.upper(): str(t) for k, t in e.items() if k.upper() in WORD})
            names[v] = n; zones[v] = z
    for f in glob.glob(os.path.join(ROOT, "ЗОНЫ", "*", "клетки.csv")):
        z = os.path.basename(os.path.dirname(f))
        for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
            p = l.split(";")
            if len(p) < 3: continue
            v = p[0]; names[v] = p[1]; zones[v] = z
            for kv in p[2].split(","):
                if "=" in kv:
                    k, t = kv.split("=", 1)
                    if k in DIRW: G.setdefault(v, {})[DIRW[k]] = t
    return G, names, zones


def parse(path):
    out = []
    for l in open(path, encoding="cp1251", errors="replace").read().splitlines():
        s = l.strip()
        if not s: continue
        if s.startswith(".триг") or s.startswith(".пауза") or s.startswith("#") or s.startswith(".") :
            out.append(("trig", s)); continue
        w = s.split()
        if w[0].lower() in ("подкр", "красться") and len(w) > 1 and w[1].lower() in DIRW:
            out.append(("step", DIRW[w[1].lower()], s)); continue
        if w[0].lower() in DIRW and len(w) == 1:
            out.append(("step", DIRW[w[0].lower()], s)); continue
        out.append(("cmd", s))
    return out


def resync(G, steps, i, look=12):
    """Найти клетку, из которой следующие шаги (до look штук, до первого .триг-переезда) проходят. Вернуть номер или None."""
    seq = []
    for t in steps[i:]:
        if t[0] == "step": seq.append(t[1])
        elif t[0] in ("trig", "cmd") and MOVE_TRIG.search(t[1]): break
        if len(seq) >= look: break
    if len(seq) < 3: return None
    cand = []
    for v in G:
        cur = v; ok = True
        for d in seq:
            nx = G.get(cur, {}).get(d)
            if not nx: ok = False; break
            cur = nx
        if ok: cand.append(v)
    return cand[0] if len(cand) == 1 else None


def check(path, start="100001", G=None, names=None, zones=None, write=None):
    if G is None: G, names, zones = graph()
    steps = parse(path)
    cur = start; res = {"steps": 0, "known": 0, "bad": [], "lost": 0, "zones": [], "out": []}
    lost = False
    for i, t in enumerate(steps):
        if t[0] == "step":
            res["steps"] += 1
            if lost or cur is None:
                cur = resync(G, steps, i)
                lost = cur is None
                if cur and res["out"] is not None: pass
            if cur and not lost:
                nx = G.get(cur, {}).get(t[1])
                res["out"].append("#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}" % (cur, cur, t[2]))
                res["known"] += 1
                if nx:
                    z = zones.get(nx)
                    if z and (not res["zones"] or res["zones"][-1] != z): res["zones"].append(z)
                    cur = nx
                else:
                    res["bad"].append("шаг %d: из %s «%s» нет выхода %s" % (i + 1, cur, names.get(cur, "?"), WORD[t[1]]))
                    cur = None; lost = True
            else:
                res["out"].append(t[2])
        else:
            res["out"].append(t[1])
            if MOVE_TRIG.search(t[1]):
                cur = None; lost = True; res["lost"] += 1
    if write:
        open(write, "w", encoding="cp1251", errors="replace").write("\n".join(res["out"]) + "\n")
    return res


VN = re.compile(r"#if \{\$MsdpRoomVnum == (\d+)\} \{([^}]*)\}")


def check_vnum(path, G, names, zones):
    """Маршрут с номерами клеток: у каждого шага клетка N, выход есть, следующий шаг — из той клетки, куда ведёт выход."""
    rows = []
    for l in open(path, encoding="cp1251", errors="replace").read().splitlines():
        m = VN.search(l)
        if m:
            cmd = m.group(2).split(";")[-1].strip().lower()
            w = cmd.split()
            d = DIRW.get(w[-1]) if w and (len(w) == 1 or w[0] in ("подкр", "красться")) else None
            rows.append((m.group(1), d, cmd))
        elif l.strip().startswith(".триг") and MOVE_TRIG.search(l):
            rows.append((None, None, l.strip()))
    r = {"steps": 0, "nomap": 0, "noexit": [], "jump": [], "zones": []}
    for i, (v, d, cmd) in enumerate(rows):
        if v is None or d is None: continue
        r["steps"] += 1
        z = zones.get(v)
        if z and (not r["zones"] or r["zones"][-1] != z): r["zones"].append(z)
        if v not in G: r["nomap"] += 1; continue
        nx = G[v].get(d)
        if not nx:
            r["noexit"].append("%s «%s» нет выхода %s" % (v, names.get(v, "?"), WORD[d])); continue
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if nxt and nxt[0] and nxt[0] != nx:
            r["jump"].append("%s %s -> %s, а следующий шаг из %s" % (v, WORD[d], nx, nxt[0]))
    return r


if __name__ == "__main__":
    if sys.argv[1] == "--vnum":
        G, names, zones = graph()
        for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.botp"))):
            if os.path.getsize(f) == 0 or os.path.basename(f).startswith("эксплор_"): continue
            txt = open(f, encoding="cp1251", errors="replace").read()
            if "MsdpRoomVnum ==" not in txt:
                print("%-28s без номеров клеток" % os.path.basename(f)[:-5]); continue
            r = check_vnum(f, G, names, zones)
            print("%-28s шагов %4d  нет в карте %3d  нет выхода %2d  разрывов %2d  зоны: %s" % (
                os.path.basename(f)[:-5], r["steps"], r["nomap"], len(r["noexit"]), len(r["jump"]), " > ".join(r["zones"][:5])))
            for b in (r["noexit"] + r["jump"])[:2]: print("      ", b)
        sys.exit()
    a = sys.argv[1:]
    if a and a[0] == "--all":
        d = a[1]; st = a[2] if len(a) > 2 else "100001"
        G, names, zones = graph()
        print("клеток в графе:", len(G))
        for f in sorted(glob.glob(os.path.join(d, "*.botp"))):
            if os.path.getsize(f) == 0: continue
            r = check(f, st, G, names, zones)
            pct = 100 * r["known"] // max(1, r["steps"])
            print("%-28s шагов %4d  с номером %3d%%  ошибок %2d  переездов %2d  зоны: %s" % (
                os.path.basename(f)[:-5], r["steps"], pct, len(r["bad"]), r["lost"], " > ".join(r["zones"][:6])))
            for b in r["bad"][:2]: print("      ", b)
    else:
        f = a[0]; st = a[1] if len(a) > 1 and not a[1].startswith("--") else "100001"
        w = a[a.index("--write") + 1] if "--write" in a else None
        r = check(f, st, write=w)
        print("шагов", r["steps"], "с номером", r["known"], "переездов", r["lost"])
        print("зоны:", " > ".join(r["zones"]))
        for b in r["bad"]: print(" ", b)
