# -*- coding: utf-8 -*-
"""Эксплор зоны Айлиной через жабу (JMC БОТ АЙЛИНА): python -X utf8 -u tools/zone_explore.py кочи
Обход вглубь (DFS) по реальным клеткам (vnum из MSDP): смотреть -> название/описание/выходы/строки мобов; смотреть N. -> карточки;
по одному убивает каждый вид (кроме NOKILL) -> опыт. Вход в зону: подход по готовому V-маршруту из JMC БОТ ИНКА\\areas\\<зона>.botp
(строки до создания области), область создаётся командой из конфига. Итог: data/recon/<зона>_айлина/explore.json (+explore.log).
Остановка: файл tools/zone_explore.stop."""
import os, sys, re, time, json, collections

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # ...\Клод мад
JMC_DIR = os.path.join(BASE, "JMC БОТ АЙЛИНА")
os.environ["JMC_TARGET"] = JMC_DIR
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc  # noqa: E402

CFG = {
    "кочи": {"botp": "кочи.botp", "root": 111041, "root_dir": "S", "zone": range(153000, 153100), "area_cmd": "обл с ю",
             "nokill": r"страж|вождь|старец", "start_route_to": 111041},
}
ZN = sys.argv[1] if len(sys.argv) > 1 else "кочи"
C = CFG[ZN]
ZONE = C["zone"]
ENTRY = C["root"]

LOG = os.path.join(JMC_DIR, "claude_game.log")
OUTDIR = os.path.join(BASE, "mudbot", "data", "recon", ZN + "_айлина")
os.makedirs(OUTDIR, exist_ok=True)
JSON_OUT = os.path.join(OUTDIR, "explore.json")
TXT_LOG = os.path.join(OUTDIR, "explore.log")
STOP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zone_explore.stop")

WORD = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
BACK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
PROMPT = re.compile(r"^\d+H \d+M \d+V")
BATTLE = re.compile(r"\[[^\]]+:[^\]]+\] \[[^\]]+:[^\]]+\]")
OBJ = re.compile(r"(лежит|лежат|валяется|валяются)\s+(тут|здесь)")
TS = re.compile(r"^\d\d:\d\d:\d\d ?")

S = {"cells": {}, "cards": {}, "exp": {}, "line2name": {}, "moves": [], "blocked": [], "out_edges": [], "notes": []}
tried = set()


def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(TXT_LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def save():
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(S, f, ensure_ascii=False, indent=1)


def read_from(pos):
    with open(LOG, "rb") as f:
        f.seek(pos)
        data = f.read()
    return [TS.sub("", x.rstrip("\r")) for x in data.decode("cp1251", "replace").split("\n")]


def send(cmd, timeout=10.0, settle=0.25):
    pos = os.path.getsize(LOG)
    jmc.type_line(cmd, force=True)
    t0 = time.time(); last_change = time.time(); last_size = pos
    while time.time() - t0 < timeout:
        time.sleep(0.12)
        size = os.path.getsize(LOG)
        if size != last_size:
            last_size = size; last_change = time.time()
        lines = read_from(pos)
        echo = next((i for i, l in enumerate(lines) if l.startswith(">> ")), None)
        if echo is None:
            continue
        for j in range(echo + 1, len(lines)):
            if PROMPT.match(lines[j]) and time.time() - last_change > settle:
                return lines[echo + 1:j], lines[j]
    return read_from(pos), ""


def getvn(retries=3):
    for _ in range(retries):
        pos = os.path.getsize(LOG)
        jmc.type_line("#scr ClaudeLog.note($MsdpRoomVnum)", force=True)
        t0 = time.time()
        while time.time() - t0 < 4:
            time.sleep(0.12)
            for l in read_from(pos):
                m = re.match(r"^## (\d+)\s*$", l)
                if m:
                    return int(m.group(1))
    return None


def in_battle(prompt):
    return bool(prompt and BATTLE.search(prompt))


def wait_peace(maxs=60):
    t0 = time.time(); poked = 0
    while time.time() - t0 < maxs:
        _, pr = send("смотреть", 6)
        if not in_battle(pr):
            return True
        if time.time() - t0 > 12 and poked < 4:
            send("убить 2.", 5); poked += 1
        time.sleep(2)
    return False


def parse_room(lines):
    ls = [l for l in lines if l.strip() != ""]
    ex_i = next((i for i, l in enumerate(ls) if re.match(r"^\[ ?Exits:", l)), None)
    if ex_i is None:
        return None
    name = ls[0].strip()
    desc = " ".join(x.strip() for x in ls[1:ex_i])
    m = re.match(r"^\[ ?Exits:\s*(.*?)\s*\]", ls[ex_i])
    exits = re.findall(r"[NESWUD]", m.group(1)) if m else []
    return name, desc, exits, ls[ex_i + 1:]


def expand(rest):
    ents = []
    for l in rest:
        if OBJ.search(l) or l.startswith("["):
            continue
        m = re.search(r"\s\[(\d+)\]\s*$", l)
        n = int(m.group(1)) if m else 1
        ents += [re.sub(r"\s\[\d+\]\s*$", "", l).strip()] * n
    return ents


def short_line(l):
    return re.sub(r"\s*\.\.\..*$", "", l).strip() + " "


def parse_card(lines):
    ls = [l for l in lines if l.strip() != ""]
    if not ls or "Вы не видите" in " ".join(ls[:2]):
        return None
    m = re.match(r"^(.*?) \[уровень (\d+)\], (.+)$", ls[0].strip())
    if not m:
        return None
    card = {"name": m.group(1).strip(), "level": int(m.group(2)), "class": m.group(3).strip(), "hp": "", "mp": "", "skills": "", "desc": "", "kind": "", "state": ""}
    d = []
    for l in ls[1:]:
        if l.startswith("Хиты:"):
            mm = re.match(r"Хиты: (\d+)/(\d+), мана: (\d+)/(\d+)", l)
            if mm:
                card["hp"], card["mp"] = mm.group(2), mm.group(4)
        elif l.startswith("Навыки:"):
            card["skills"] = re.sub(r"\s+", " ", l[len("Навыки:"):]).strip()
        elif l.startswith("Вы видите перед собой"):
            card["kind"] = l.replace("Вы видите перед собой", "").strip(" .")
        elif re.search(r" в [а-я]+ состоянии\.?$", l):
            card["state"] = l.strip()
        else:
            d.append(l.strip())
    card["desc"] = " ".join(d)
    return card


def observe(vn):
    lines, pr = send("смотреть", 8)
    room = parse_room(lines) or parse_room(send("смотреть", 8)[0])
    if not room:
        say("не разобрал комнату", vn, lines[:3]); return None
    name, desc, exits, rest = room
    ents = expand(rest)
    cell = S["cells"].get(str(vn))
    if cell is None:
        cell = {"vnum": vn, "name": name, "desc": desc, "exits": exits, "edges": {}, "mobs_lines": [], "mobs": []}
        S["cells"][str(vn)] = cell
    cell["mobs_lines"] = ents
    names = []
    all_known = all(short_line(e) in S["line2name"] for e in ents)
    idx = 2
    for e in ents:
        if all_known:
            names.append(S["line2name"][short_line(e)]); idx += 1; continue
        out, _ = send("смотреть %d." % idx, 6)
        card = parse_card(out)
        if card is None:
            break
        S["cards"].setdefault(card["name"], card)
        S["line2name"].setdefault(short_line(e), card["name"])
        names.append(card["name"])
        idx += 1
    cell["mobs"] = names
    for i, nm in enumerate(names):
        if nm in S["exp"]:
            continue
        if re.search(C["nokill"], nm, re.I):
            S["exp"][nm] = -2                                  # по правилу пользователя не бьём
            continue
        pos = os.path.getsize(LOG)
        send("убить %d." % (i + 2), 8)
        t0 = time.time(); got = None
        while time.time() - t0 < 40:
            time.sleep(1.5)
            txt = "\n".join(read_from(pos))
            m = re.search(r"получили ([\d ]+?) (?:единиц|очк)\S* опыта", txt)
            if m:
                got = int(m.group(1).replace(" ", "")); break
            if re.search(r"Вы не видите|Кого вы хотите|Вы не можете", txt) and time.time() - t0 > 4:
                break
        S["exp"][nm] = got if got is not None else -1
        say("убит", nm, "опыт", got)
        wait_peace(40)
        break
    return cell


def move(d, expect_from):
    for attempt in range(5):
        lines, pr = send(WORD[d], 8)
        txt = " ".join(lines)
        if "Не получится" in txt or in_battle(pr):
            wait_peace(60); continue
        if "слишком устали" in txt:
            time.sleep(3); continue
        if "Попробуйте сначала открыть" in txt:       # триггер двери откроет, повторим ход
            time.sleep(2); continue
        vn = getvn()
        if vn is not None:
            S["moves"].append([expect_from, d, vn])
            return vn
    return getvn()


def resync(target, cur):
    if cur is None:
        return
    graph = {}
    for k, c in S["cells"].items():
        for d, n in c.get("edges", {}).items():
            graph.setdefault(int(k), {})[d] = n
            graph.setdefault(n, {})[BACK[d]] = int(k)
    prev = {cur: None}; q = collections.deque([cur])
    while q:
        v = q.popleft()
        if v == target:
            break
        for d, n in graph.get(v, {}).items():
            if n not in prev:
                prev[n] = (v, d); q.append(n)
    if target not in prev:
        say("resync: пути нет", cur, "->", target); return
    path = []; v = target
    while prev[v]:
        v, d = prev[v][0], prev[v][1]; path.append(d)
    for d in reversed(path):
        move(d, 0)


def explore(vn, depth=0):
    if os.path.exists(STOP):
        raise KeyboardInterrupt
    cell = observe(vn)
    if cell is None:
        return
    save()
    for d in cell["exits"]:
        if (vn, d) in tried:
            continue
        tried.add((vn, d))
        if vn == ENTRY and d != C["root_dir"]:
            continue
        nv = move(d, vn)
        if nv is None:
            say("не удалось узнать vnum после", d, "из", vn); continue
        if nv == vn:
            S["blocked"].append([vn, d]); continue
        cell["edges"][d] = nv
        if nv not in ZONE and nv != ENTRY:
            S["out_edges"].append([vn, d, nv])
            back = move(BACK[d], nv)
            if back != vn:
                say("после выхода за зону вернулся в", back, "ждал", vn)
            continue
        if nv == ENTRY or str(nv) in S["cells"]:
            back = move(BACK[d], nv)
            if back != vn:
                say("возврат дал", back, "ждал", vn); resync(vn, back)
            continue
        say("клетка", nv, "глубина", depth + 1, "всего клеток", len(S["cells"]) + 1)
        explore(nv, depth + 1)
        back = move(BACK[d], nv)
        if back != vn:
            say("возврат дал", back, "ждал", vn); resync(vn, back)


def arrive(target, tries=25):
    for _ in range(tries):
        time.sleep(2.5)
        v = getvn()
        if v == target:
            return v
    return getvn()


def approach_lines():
    """Команды подхода из V-маршрута зоны в JMC БОТ ИНКА\\areas: строки до создания области. -> [(vnum_где_команда, команда)]"""
    enc = "cp1251"
    ls = open(os.path.join(BASE, "JMC БОТ ИНКА", "areas", C["botp"]), encoding=enc).read().splitlines()
    out = []
    for s in ls:
        if s.startswith(".триг обл"):
            break
        m = re.search(r"\$MsdpRoomVnum == (\d+)\} \{([^{}]*)\}\s*$", s)
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def follow(steps, vn):
    """Идти по маршруту подхода кусками по 10 команд; после каждого куска сверка клетки, при сбое (бой, очистка очереди) продолжаю с текущей клетки."""
    last = 0; stuck = 0
    for _ in range(60):
        vn = getvn()
        if vn == ENTRY:
            return True
        idx = next((j for j in range(last, len(steps)) if steps[j][0] == vn), None)
        if idx is None:
            idx = next((j for j in range(len(steps)) if steps[j][0] == vn), None)
        if idx is None:
            say("потерял маршрут подхода, стою в", vn); return False
        if idx == last and stuck >= 1:
            stuck += 1
            if stuck > 6:
                say("не двигаюсь на шаге", idx, "клетка", vn); return False
        elif idx > last:
            stuck = 0
        else:
            stuck += 1
        last = max(last, idx)
        wait_peace(40)
        chunk = steps[idx:idx + 10]
        send(";".join(c for _, c in chunk), 10)
        nxt = steps[idx + 10][0] if idx + 10 < len(steps) else ENTRY
        for _ in range(8):
            time.sleep(1.5)
            if getvn() == nxt:
                break
    return getvn() == ENTRY


def leave_luga(vn):
    """Из Заливных лугов (140xxx) на склад Элендора: по рёбрам эксплора луга до 137220, дальше спидволк назад."""
    P = os.path.join(BASE, "mudbot", "data", "recon", "луга_айлина", "explore.json")
    L = json.load(open(P, encoding="utf-8"))
    g = collections.defaultdict(dict)
    for frm, d, to in L["moves"]:
        if frm and to:
            g[frm][d] = to
            g[to].setdefault(BACK[d], frm)
    prev = {vn: None}; q = collections.deque([vn])
    while q:
        v = q.popleft()
        if v == 137220:
            break
        for d, n in g.get(v, {}).items():
            if n not in prev:
                prev[n] = (v, d); q.append(n)
    if 137220 not in prev:
        say("путь из лугов не найден"); return False
    path = []; v = 137220
    while prev[v]:
        v, d = prev[v][0], prev[v][1]; path.append(d)
    cmds = [WORD[d] for d in reversed(path)]
    say("выхожу из луга:", len(cmds), "ходов")
    for i in range(0, len(cmds), 25):
        send(";".join(cmds[i:i + 25]), 10)
        time.sleep(1)
    if arrive(137220, 30) != 137220:
        say("не дошёл до 137220"); return False
    send("вверх" if False else ";".join(["север"] * 17 + ["восток", "север"] + ["запад"] * 11), 10)   # обратно 11esw17s
    if arrive(100009, 30) != 100009:
        say("не дошёл до ЦП"); return False
    send("север;север;север;север;запад;запад;север", 10)
    return arrive(100076, 20) == 100076


def main():
    if os.path.exists(STOP):
        os.remove(STOP)
    say("эксплор", ZN, "запущен; лог игры:", LOG)
    vn = getvn()
    say("сейчас в клетке", vn)
    if vn in range(140000, 140300) or vn == 137220:
        if not leave_luga(vn):
            return
        vn = getvn(); say("после выхода из лугов:", vn)
    if vn != ENTRY and vn not in ZONE:
        steps = approach_lines()
        if vn != 100076 and vn not in [v for v, _ in steps]:
            say("не на маршруте подхода:", vn); return
        say("подход:", len(steps), "команд, старт с клетки", vn)
        if not follow(steps, vn):
            return
        vn = getvn(); say("у входа:", vn)
        lines, _ = send(C["area_cmd"], 10)
        say("область:", " | ".join(l for l in lines if "экземпляр" in l or "сможете" in l)[:200])
        time.sleep(1.5)
    if vn != ENTRY and vn not in ZONE:
        say("не у входа в зону:", vn, "- стоп"); return
    try:
        explore(vn)
    except KeyboardInterrupt:
        say("остановлено по стоп-файлу")
    save()
    say("ГОТОВО. клеток:", len(S["cells"]), "видов мобов:", len(S["cards"]), "опыт по видам:", len(S["exp"]))


if __name__ == "__main__":
    sys.setrecursionlimit(5000)
    main()

