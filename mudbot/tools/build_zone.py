"""Сборка зоны для бота из лога эксплора Айлины: клетки -> game.db (rooms), карточки -> game.db (mob_cards), маршрут .botp.
Запуск: python -X utf8 tools/build_zone.py <ключ>   (ключ из ZONES)
Переходы берутся из Logs\\game_<дата>.log жабы Айлины: '>> <команда движения>' и следующая за ней запись '## <vnum>' (её пишет step_vn.py/explore.py)."""
import os, re, sys, json, sqlite3, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGDIR = os.path.join(os.path.dirname(ROOT), "JMC БОТ АЙЛИНА", "Logs")
DB = os.path.join(ROOT, "data", "game.db")
DIRW = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вверх": "вверх", "вниз": "вниз"}
OPP = {"с": "ю", "ю": "с", "в": "з", "з": "в", "вверх": "вниз", "вниз": "вверх"}
EXITKEY = {"с": "N", "ю": "S", "в": "E", "з": "W", "вверх": "U", "вниз": "D"}

ZONES = {
    "башня_вихря": dict(name="Башня вихря", prefix=159, start=159001, exclude=lambda v: v >= 159062,
                        create_hub=303067, create_cmd="обл с с", exit_cmd="ю", approach_from=301041,
                        approach_path="путь Вход в зону Башня вихря",
                        late={(159009, "в"), (159007, "ю"), (159011, "с"), (159005, "з")}),
    "рубеж": dict(name="Рыцарский рубеж", prefix=380, start=380094, exclude=lambda v: v in (380091, 380095),
                  create_hub=303094, create_cmd="обл с з", exit_cmd="в", approach_from=301041,
                  late={(380010, "ю")},
                  doors={(380035, "в"): ["откр решетка в"], (380038, "в"): ["откр решетка в"], (380065, "з"): ["откр кованая з"],
                         (380010, "ю"): ["отпер дуб ю", "откр дуб ю"]}),
    "логово_орды": dict(name="Логовище орды", prefix=302, start=302001, exclude=lambda v: False,
                        create_hub=303096, create_cmd="обл с з", exit_cmd="в", approach_from=301041),
}
# названия клеток Логова (снято вручную 14.11, explore.jsonl для него нет)
LOGOVO_NAMES = {302001: "Гнилой лес", 302002: "Гнилой лес", 302003: "Большая проплешина", 302004: "Большая проплешина", 302005: "Спуск в Дыру",
                302006: "В круглом туннеле", 302007: "Изгиб туннеля", 302008: "Покрытый слизью туннель", 302009: "Вонючий туннель",
                302010: "Вонючий туннель", 302011: "Черная дыра", 302012: "Первое Логовище орды", 302020: "Смертельная западня",
                302019: "Черный лаз", 302018: "Изгиб туннеля", 302017: "Овальный туннель", 302016: "Резкий поворот",
                302014: "Вонючий проход", 302015: "Лаз вниз"}


def transitions(date):
    f = os.path.join(LOGDIR, f"game_{date}.log")
    tr = {}                       # (from, dir) -> to
    last = None; moves = []
    for raw in open(f, "rb").read().decode("cp1251", errors="replace").splitlines():
        l = re.sub(r"^\d\d:\d\d:\d\d ", "", raw).strip()
        m = re.match(r"^>> (.+)$", l)
        if m:
            c = m.group(1).strip()
            if c in DIRW:
                moves.append(c)
            elif "ClaudeLog.note" not in c and not re.match(r"^(см|огл|экип|инв|сч|обл|откр|отпер|убить|взя|од|осуш|кз|кс|путь|ехать|аф|осм|склад|забрать|вниз|вверх)", c):
                moves = []        # прочие команды (в т.ч. ввод пользователя): цепочку движений не ведём
            continue
        m = re.match(r"^## (\d+)$", l)
        if m:
            n = int(m.group(1))
            if last is not None and moves:
                cur = last; ok = True
                for i, d in enumerate(moves):
                    nxt = tr.get((cur, d))
                    if i == len(moves) - 1:
                        if cur != n:
                            tr[(cur, d)] = n
                            tr.setdefault((n, OPP[d]), cur)
                        break
                    if nxt is None:
                        ok = False; break
                    cur = nxt
            last = n; moves = []
    return tr


def load_rooms(zone):
    rows = {}
    p = os.path.join(ROOT, "data", "recon", zone, "explore.jsonl")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            rows[r["vnum"]] = r
    return rows


def main(key, date):
    z = ZONES[key]
    tr = transitions(date)
    rooms = load_rooms(key)
    if key == "логово_орды":
        for v, n in LOGOVO_NAMES.items():
            rooms.setdefault(v, {"vnum": v, "имя": n, "выходы": [], "строки": [], "карточки": [], "убито": []})
    pre = z["prefix"]
    inz = lambda v: v // 1000 == pre and not z["exclude"](v)
    adj = collections.defaultdict(dict)
    for (a, d), b in tr.items():
        if inz(a) and inz(b):
            adj[a][d] = b
    nodes = set(adj) | {b for a in adj for b in adj[a].values()} | {v for v in rooms if inz(v)}
    # ---- база: rooms
    db = sqlite3.connect(DB)
    for v in sorted(nodes):
        name = rooms.get(v, {}).get("имя") or ""
        ex = {EXITKEY[d]: str(t) for d, t in adj.get(v, {}).items()}
        db.execute("delete from rooms where vnum=?", (str(v),))
        db.execute("insert into rooms(vnum,zone,name,exits,note,source) values(?,?,?,?,?,?)", (str(v), z["name"], name, json.dumps(ex, ensure_ascii=False), "", "explore_14-11"))
    # ---- база: mob_cards
    db.execute("delete from mob_cards where zone=? and room in (select name from rooms where zone=?) and 0", (z["name"], z["name"]))
    seen = set()
    n_cards = 0
    for v, r in rooms.items():
        cards = {c["имя"]: c for c in r.get("карточки", [])}
        for k in r.get("убито", []):
            cards.setdefault(k["имя"], k)
        for nm, c in cards.items():
            if (z["name"], nm) in seen:
                continue
            seen.add((z["name"], nm))
            line = next((s for s in r.get("строки", []) if nm.lower().split()[0] in s.lower()), "")
            hp = c.get("хп")
            db.execute("delete from mob_cards where zone=? and name=?", (z["name"], nm))
            db.execute("insert into mob_cards(zone,name,level,prof,hp,mana,skills,kind,desc,room) values(?,?,?,?,?,?,?,?,?,?)",
                       (z["name"], nm, c.get("лвл"), c.get("проф"), f"{hp}/{hp}" if hp else "", "", c.get("навыки", ""), "", line, r["имя"]))
            n_cards += 1
    db.commit()
    # ---- маршрут: обход в глубину по графу
    route = []                    # (vnum_before, dir)
    vis = set()
    late = z.get("late", set())   # двери с ключом с мобов: проходим в самом конце

    def dfs(v):
        vis.add(v)
        for d, t in sorted(adj.get(v, {}).items(), key=lambda it: ((v, it[0]) in late, it[0])):
            if t in vis:
                continue
            route.append((v, d)); dfs(t); route.append((t, OPP[d]))
    dfs(z["start"])
    # двери: (vnum, направление) -> команды открытия (справка ДВЕРИ: открыть <дверь> [направление])
    doors = dict(z.get("doors", {}))
    dj = os.path.join(ROOT, "data", "recon", key, "doors.jsonl")
    if os.path.exists(dj):
        for l in open(dj, encoding="utf-8"):
            d = json.loads(l)
            if d.get("итог", "").startswith("открыто") and d.get("дверь"):
                kw = d["дверь"].split()[0][:4]
                dl = {"N": "с", "S": "ю", "E": "в", "W": "з", "U": "вверх", "D": "вниз"}[d["направление"]]
                doors[(d["vnum"], dl)] = [f"отпер {kw} {dl}", f"откр {kw} {dl}"]
    # подход: от approach_from до create_hub по графу дороги (303xxx)
    road = collections.defaultdict(dict)
    for (a, d), b in tr.items():
        road[a][d] = b
    def bfs(src, dst):
        prev = {src: None}; q = collections.deque([src])
        while q:
            u = q.popleft()
            if u == dst:
                break
            for d, t in road.get(u, {}).items():
                if t not in prev:
                    prev[t] = (u, d); q.append(t)
        if dst not in prev:
            return None
        p = []; c = dst
        while prev[c]:
            p.append((prev[c][0], prev[c][1])); c = prev[c][0]
        return p[::-1]
    appr = bfs(z["approach_from"], z["create_hub"])
    L = [".триг #scr botCore.BotInZone = false"]
    chk = lambda v, cmd: "#if {$MsdpRoomVnum != %d} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %d} {%s}" % (v, v, cmd)
    if appr:
        L.append(chk(appr[0][0], ";".join(DIRW[d] for _, d in appr)))
    elif z.get("approach_path"):
        # дорога до входа пройдена игровым `путь` (ходьба без шагов в логе): з на дорогу и `путь Вход в зону ...`
        L.append(chk(z["approach_from"], "запад;" + z["approach_path"] + ";#scr botCore.wait(80)"))
    else:
        L.append("# ПОДХОД НЕ НАЙДЕН в логе: от %d до %d" % (z["approach_from"], z["create_hub"]))
    L.append(".триг " + z["create_cmd"])
    L.append(".триг #scr botCore.BotInZone = true")
    for v, d in route:
        L.append(chk(v, ";".join(doors.get((v, d), []) + [DIRW[d]])))      # команды двери только когда я в нужной клетке
    L.append(chk(z["start"], DIRW[z["exit_cmd"]]))
    L.append(".триг #scr botCore.BotInZone = false")
    out = os.path.join(ROOT, "data", "recon", key, f"{key}.botp")
    open(out, "w", encoding="cp1251", errors="replace", newline="").write("\r\n".join(L) + "\r\n")
    print(key, "клеток", len(nodes), "карточек", n_cards, "шагов маршрута", len(route), "подход", len(appr) if appr else None, "->", out)
    missing = [v for v in nodes if v not in vis]
    print("недостижимые в графе:", missing)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat())
