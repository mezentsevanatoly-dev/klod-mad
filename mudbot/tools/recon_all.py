"""Автономная разведка зон по логам пользователя (v2): подход от площади города, область, обход mapfight --survey (бьёт всех
по миникарте, карточки и опыт в game.db), V-маршрут по реальным клеткам боя из MSDP (out.log), csv и заметки.

python -X utf8 tools/recon_all.py [лог ...]      (без аргументов: вся очередь QUEUE, не дольше 10 часов)
Журнал: tools/recon_all.log, состояние: data/recon/_status.json. Смерть в зоне -> зона помечается; кулдаун области -> в конец
очереди. Проверку присутствия решает человек (окно). Вход проверяется по названию созданного экземпляра (EXPECT).
"""
import ast
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import log_prep  # noqa: E402
import mk_v_from_route as mkv  # noqa: E402

RECON = os.path.join(ROOT, "data", "recon")
DBPATH = os.path.join(ROOT, "data", "game.db")
STATUS = os.path.join(RECON, "_status.json")
OUTLOG = os.path.join(ROOT, "out.log")
ENV = dict(os.environ, MUD_VIA="bot")
HUB = {"e": "100009", "g": "115039", "o": "180154"}        # площади Элендора / Геоланта, Повозки в Огисе (приезд `ехать огис`)
BETWEEN = {("g", "e"): "22w3n7wn22w", ("e", "g"): "22es7e3s22e"}
# лог: (хаб, спидволк до клетки входа, клетка входа, как называется созданный экземпляр)
BASE_STEP = {"луга": "юг", "порт": "запад", "огис_конюшни": "запад"}               # зоны без области: шаг от клетки входа внутрь зоны
EXTRA_ARGS = {"рыбка": ["--never", "торговец"]}   # квесты не делаем, бьём всех мобов (Контар, капитан, отшельник — тоже), торговец мирный
QUEUE = [
    ("луга", "e", "11esw17s", "137220", None),
    ("порт", "e", "3w5s", "100053", None),
    ("рыбка", "e", "20e8se2s2e2sw2s2e2s", "111080", "рыбак"),
    ("огис_лечеб", "o", "wn4e3nwuw2n", "180048", "Лечебниц"),
    ("огис_конюшни", "o", "wn2esds3w", "180025", None),
    ("бесы", "e", "16e8nw5n3wn", "105003", "бес"),
    ("24+", "g", "8sese3sw2s3e", "94115", "Лис"),
    ("кочи", "e", "20e8s2w2sw2sw7sw3sese", "111041", "очевник"),
    ("ящеры", "g", "21w7ne6ne", "109028", "человекоящер"),
    ("привы2", "g", "9ne2ne2ne", "122011", "привиден"),
    ("чайный_домик", "g", "5s4w", "115064", "Чайн"),
    ("каналгео1", "g", "2nw", "115042", "Катаком"),
    ("парк", "e", "nw", "100167", "'Парк'"),
    ("аллея", "e", "4nw", "100069", "Аллея"),
    ("канал", "e", "5e3sw", "100121", "Канализац"),
    ("притон", "e", "5e3s2wn", "100011", "Притон"),
    ("привы1", "g", "9ne2ne2ne", "122011", "привиден"),
    ("склад1", "g", "4e4se", "115080", "Склад"),
    ("геоканал3", "g", "2nw", "115042", "Катаком"),
]
LOGF = open(os.path.join(HERE, "recon_all.log"), "a", encoding="utf-8")


def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    LOGF.write(s + "\n")
    LOGF.flush()
    print(s, flush=True)


def cmd(c, timeout=420):
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "cmd.py"), c], env=ENV, cwd=ROOT, capture_output=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return r.stdout + r.stderr


def cur():
    out = cmd("смотреть", 60)
    m = re.findall(r"^\[cur\] (\{.*\})\s*$", out, re.M)
    return ast.literal_eval(m[-1]) if m else {}


def go(vnum):
    return "пришли:" in cmd(f"!go {vnum}")


def inv(path):
    d = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"}
    return "".join(f"{n}{d[ch]}" for n, ch in reversed(re.findall(r"(\d*)([nsewud])", path)))


def to_hub(kind):
    """Дойти до центральной площади нужного города (между городами — спидволк, внутри города — !go)."""
    c = cur()
    if kind == "o":                                        # Огис: повозкой из Элендора, приезжаем в «Повозки»
        if "Огис" not in c.get("area", ""):
            if not to_hub("e") or not go("100147"):
                return False
            cmd("ехать огис|20")
            for _ in range(24):
                time.sleep(5)
                if "Огис" in cur().get("area", ""):
                    break
        return go(HUB["o"]) and cur().get("vnum") == HUB["o"]
    here = "e" if "Элендор" in c.get("area", "") else "g" if "Геолант" in c.get("area", "") else None
    if here and here != kind:
        go(HUB[here])
        cmd("!sw " + BETWEEN[(here, kind)])
    elif not go(HUB[kind]):
        other = "e" if kind == "g" else "g"
        if not go(HUB[other]):
            return False
        cmd("!sw " + BETWEEN[(other, kind)])
    return cur().get("vnum") == HUB[kind]


def feed_needs():
    out = cmd("сч", 60)
    if "хотите есть" in out or "хотите пить" in out:
        cmd("осуш насы|3", 60)
        say("насыщение выпито")


def load_status():
    try:
        return json.load(open(STATUS, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_status(st):
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def run_map(name):
    """Обход зоны mapfight (бьёт мобов из лога по миникарте). Возврат ok / dead / fail."""
    args = [sys.executable, "-X", "utf8", os.path.join(HERE, "mapfight.py"), "99", "--survey", "--extra", "1", "--below", "99", "--skip", "0",
            "--route", name] + EXTRA_ARGS.get(name, [])
    try:
        r = subprocess.run(args, env=ENV, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace", timeout=3000)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        say(name, "mapfight >50 мин, стоп")
        return "fail"
    for l in out.splitlines()[-12:]:
        say("   ", l.strip()[:180])
    if "ПОГИБ" in out or "мертв" in out.lower() and "Вы мертвы" in out:
        return "dead"
    return "ok" if "зона пройдена" in out else "fail"


def parse_run(offset):
    """Из out.log после offset: граф комнат (exits), порядок посещения и клетки убийств (R.I.P. -> текущая клетка)."""
    g, kills, visited, curv = {}, {}, [], None
    rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")
    with open(OUTLOG, "rb") as f:
        f.seek(0)
        for line in f.read().decode("utf-8", errors="replace").splitlines():
            m = rx.match(line)
            if m:
                try:
                    ex = ast.literal_eval(m.group(4))
                except Exception:
                    continue
                g[m.group(1)] = (m.group(2).strip(), m.group(3).strip(), {k.upper(): str(v) for k, v in ex.items()})
    with open(OUTLOG, "rb") as f:
        f.seek(offset)
        for line in f.read().decode("utf-8", errors="replace").splitlines():
            m = rx.match(line)
            if m:
                curv = m.group(1)
                if not visited or visited[-1] != curv:
                    visited.append(curv)
            elif "R.I.P." in line and curv:
                kills[curv] = kills.get(curv, 0) + 1
    return g, kills, visited


def bfs(g, a, b):
    prev, q = {a: None}, deque([a])
    while q:
        v = q.popleft()
        if v == b:
            break
        for d, t in g.get(v, ("", "", {}))[2].items():
            if t in g and t not in prev:
                prev[t] = (v, d)
                q.append(t)
    if b not in prev:
        return None
    path, v = [], b
    while prev[v]:
        v, d = prev[v][0], prev[v][1]
        path.append(d)
    return path[::-1]


_RX = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")


def kills_in_area(area_name):
    """Клетки убийств (R.I.P. -> текущая клетка) только внутри зоны area_name, по всему out.log."""
    kills, curv, cura = {}, None, None
    for line in open(OUTLOG, encoding="utf-8", errors="replace"):
        m = _RX.match(line)
        if m:
            curv, cura = m.group(1), m.group(2).strip()
        elif "R.I.P." in line and curv and cura == area_name:
            kills[curv] = kills.get(curv, 0) + 1
    return kills


def last_inner(entry):
    """Первая клетка зоны после входа: последний переход entry -> клетка другой зоны в out.log."""
    seq = []
    for line in open(OUTLOG, encoding="utf-8", errors="replace"):
        m = _RX.match(line)
        if m:
            seq.append((m.group(1), m.group(2).strip()))
    for i in range(len(seq) - 2, -1, -1):
        if seq[i][0] == entry and seq[i + 1][1] != seq[i][1]:
            return seq[i + 1][0]
    return None


def build_tour(name, kind, sw, entry, area_cmd, offset):
    """V по реальному обходу: клетки с убийствами в порядке ближайшего соседа, пути по графу MSDP, возврат ко входу и на площадь."""
    D2R = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
    g, kills, visited, = parse_run(offset or 0)
    if offset is None:                                      # пересборка без прогона: последний переход вход -> зона по истории out.log
        kills, inner = {}, last_inner(entry)
    else:
        inner = next((v for v in visited if v != entry), None)
    if inner is None or entry not in g or inner not in g:
        return "V не собран: нет входа в графе"
    for v, c in kills_in_area(g[inner][0]).items():          # клетки боя за всю историю лога в этой зоне (мобы без репопа в инсте уже убиты)
        kills[v] = max(kills.get(v, 0), c)
    if not kills:
        return "V не собран: убийств не было"
    # клетка входа -> первая клетка зоны: выход, который ведёт в зону (после создания области)
    first = next((d for d, t in g[entry][2].items() if t == inner), None)
    if first is None:
        return f"V не собран: из {entry} нет выхода в {inner}"
    todo, cell, route = dict(kills), inner, []
    order = []
    while todo:
        best = None
        for v in todo:
            p = bfs(g, cell, v) if v != cell else []
            if p is not None and (best is None or len(p) < len(best[1])):
                best = (v, p)
        if best is None:
            order.append(("потеряна", next(iter(todo))))
            break
        v, p = best
        route += [(D2R[d]) for d in p]
        cell = v
        order.append((v, todo.pop(v)))
    back = bfs(g, cell, inner) if cell != inner else []
    if back is None:
        return f"V не собран: нет пути {cell} -> {inner}"
    moves = [D2R[first]] + route + [D2R[d] for d in back]
    items = [("move", m) for m in mkv.expand(sw)] + ([("cmd", ".триг обл с " + area_cmd)] if area_cmd else [])
    items += [("move", m) for m in moves]
    items += [("move", {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}[D2R[first]])]
    items += [("move", m) for m in [{"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}[x]
                                    for x in reversed(mkv.expand(sw))]]
    lines, cell = [], HUB[kind]
    for k, val in items:
        if k == "cmd":
            lines.append(val)
            continue
        nxt = g.get(cell, ("", "", {}))[2].get(mkv.D[val])
        if not nxt or nxt not in g:
            return f"V не собран: ход «{val}» из {cell} вне графа (подход/возврат)"
        lines.append(mkv.V.format(v=cell, cmd=val))
        cell = nxt
    d = os.path.join(RECON, name)
    open(os.path.join(d, f"рр_{name}V.botp"), "w", encoding="cp1251", newline="\r\n").write("\n".join(lines) + "\n")
    plain = []
    for l in lines:
        m = re.search(r"== \d+\} \{(.*)\}$", l)
        plain.append(m.group(1) if l.startswith("#if") and m else l)
    open(os.path.join(d, f"рр_{name}.botp"), "w", encoding="cp1251", newline="\r\n").write("\n".join(plain) + "\n")
    with open(os.path.join(d, f"рр_{name}V.trace.txt"), "w", encoding="utf-8") as f:
        f.write("клетки убийств (vnum: убито): " + ", ".join(f"{v}:{c}" for v, c in order if v != "потеряна") + "\n")
        f.write("название клетки: " + "; ".join(f"{v}={g[v][1]}" for v, _ in order if v in g) + "\n")
    return f"V собран: {len(lines)} строк, {len(kills)} клеток боя, конец {cell} ({'хаб' if cell == HUB[kind] else 'НЕ хаб'})"


def finish_csv(name):
    """csv мобов: карточки и опыт из game.db (результат обхода); мобы выше моего уровня+1 в csv не входят."""
    import csv
    db = sqlite3.connect(DBPATH)
    p = os.path.join(RECON, name, name + "_mob.csv")
    rows = list(csv.reader(open(p, encoding="cp1251"), delimiter=";"))
    out, dropped = [rows[0]], []
    for r in rows[1:]:
        c = db.execute("select level,prof,hp,mana,skills from mob_cards where name=? order by rowid desc limit 1", (r[0],)).fetchone()
        if c:
            r[8], r[12] = str(c[0] or r[8]), c[1] or r[12]
            if c[2]:
                r[2] = r[3] = str(c[2]).split("/")[-1]
            r[11] = c[4] or ""
        lv = int(r[8]) if str(r[8]).isdigit() else 0
        if lv > 26:
            dropped.append(f"{r[0]} ({lv})")
            continue
        e = db.execute("select avg(exp) from mob_kills where name=? and my_level>=25 and exp>0", (r[0],)).fetchone()[0]
        if e:
            r[6] = str(int(e))
        out.append(r)
    with open(os.path.join(RECON, name, f"рр_{name}V_mob.csv"), "w", encoding="cp1251", errors="replace", newline="") as f:
        csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n").writerows(out)
    return len(out) - 1, dropped


def zone(name, kind, sw, entry, expect, st):
    log_prep.prep(name, sqlite3.connect(DBPATH))
    route = json.load(open(os.path.join(RECON, name, name + "_route.json"), encoding="utf-8"))["steps"]
    k = next((i for i, s in enumerate(route) if s.get("cmd", "").startswith("область создать")), None)
    if k is None and expect is not None:
        return "нет «область создать» в логе"
    if expect is None:                                    # зона без области: просто входим
        d, short, c = BASE_STEP[name], None, []
    else:
        c = route[k]["cmd"].split()
        d = c[2] if len(c) > 2 and "<" not in c[2] else next((s["move"] for s in route[k + 1:] if "move" in s), "с")
        short = {"север": "с", "юг": "ю", "восток": "в", "запад": "з", "вверх": "вв", "вниз": "вн", "вни": "вн"}.get(d, d)
    json.dump({"start": None, "steps": route}, open(os.path.join(ROOT, "data", "db", "routes", name + ".json"), "w",
              encoding="utf-8"), ensure_ascii=False)
    feed_needs()
    if not to_hub(kind):
        return "не дошла до площади"
    cmd("!sw " + sw)
    if cur().get("vnum") != entry and not go(entry):
        return f"не дошла до входа {entry}"
    zname = name
    if expect is not None:
        say(name, "у входа, создаю область", d)
        out = cmd(f"область создать {d}|6")
        if "сможете создать новый экземпляр" in out:
            tbl = cmd("область|4")                        # та же фраза и при активной области: смотрим таблицу `область`
            alive = [l for l in tbl.splitlines() if "активен" in l and expect.strip("'") in l]
            if not alive:
                m = re.search(r"через (\d+)", out)
                st[name] = {"wait": int(m.group(1)) if m else 30, "t": time.time()}
                return "КД"
            out = f"экземпляр зоны '{alive[0].split(None, 2)[2].rsplit('  ', 2)[0].strip()}'"
        m = re.search(r"экземпляр зоны '([^']+)'", out)
        zname = m.group(1) if m else ""
        if expect.strip("'") not in zname or (expect.startswith("'") and zname != expect.strip("'")):
            cmd(f"область удалить {d}|4")
            return f"создался экземпляр «{zname}», ожидали {expect}: удалила, зона на ручной разбор"
    offset = os.path.getsize(OUTLOG)
    full = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}.get(short, d)
    cmd(f"{full}|3")                                     # шаг внутрь зоны: обход начинается в её клетке, не на входе
    if cur().get("area", "").startswith("Город"):
        return f"после шага «{full}» осталась в городе: проверить вход вручную"
    res = run_map(name)
    say(name, "обход:", res)
    nm, dropped = finish_csv(name)
    vmsg = build_tour(name, kind, sw, entry, short, offset) if res != "dead" else "V не собран: персонаж погиб"
    say(name, vmsg)
    if res != "dead":
        go(entry)
        cmd("!sw " + inv(sw))
    with open(os.path.join(RECON, name, f"Разведка_{name}.md"), "w", encoding="utf-8") as f:
        f.write(f"# {name}: разведка Айлиной {time.strftime('%d.%m.%Y %H:%M')}\n\n- зона: {zname}; обход: {res}\n- {vmsg}\n"
                f"- мобов в csv: {nm}; не в csv (выше лвл+1): {', '.join(dropped) or 'нет'}\n"
                f"- вход {entry}, область `{short}`, подход {sw}\n- разбор лога: {name}.md, маршрут пользователя: {name}_route.json\n"
                f"- V собран по реальным клеткам боя (маршрут лога не ложится на граф), квестовые действия зоны не включены\n")
    return f"{res}; {vmsg}; csv {nm}"


def main():
    only = sys.argv[1:]
    st = load_status()
    q = deque(z for z in QUEUE if not only or z[0] in only)
    deadline = time.time() + 10 * 3600
    idle = 0
    while q and time.time() < deadline:
        name, kind, sw, entry, expect = q.popleft()
        if st.get(name, {}).get("done"):
            continue
        w = st.get(name, {})
        if w.get("wait") and time.time() - w["t"] < w["wait"] * 60:
            q.append((name, kind, sw, entry, expect))
            idle += 1
            if idle >= len(q):
                time.sleep(120)
                idle = 0
            continue
        idle = 0
        say("=== зона", name)
        try:
            r = zone(name, kind, sw, entry, expect, st)
        except Exception as e:
            import traceback
            say(name, "ИСКЛЮЧЕНИЕ", repr(e), traceback.format_exc()[-600:])
            r = "исключение"
        say(name, "итог:", r)
        if r == "КД":
            q.append((name, kind, sw, entry, expect))
        else:
            st[name] = {"done": True, "result": r}
        save_status(st)
    say("очередь окончена")


if __name__ == "__main__":
    main()
