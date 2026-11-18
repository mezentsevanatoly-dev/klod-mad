"""Подготовка зон из логов пользователя (JMC\\<имя>, cp1251) -> data/recon/<имя>/.

python -X utf8 tools/log_prep.py [имя_лога ...]     (без аргументов: все логи этапов)
Для каждого лога: <имя>.md (уровень, комнаты, убийства и опыт, особые команды), <имя>_cmds.txt (все команды по порядку,
с комнатой, где они набраны), <имя>_mob.csv (формат Bot_ZayNew; Hp/профа/уровень из mob_cards, описание из комнат лога).
Ничего не отправляет в игру. Клеток (vnum) в логах JMC нет: привязка к MSDP — при разведке в клиенте.
"""
import csv
import os
import re
import sqlite3
import sys
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
OUT = os.path.join(ROOT, "data", "recon")
SKIP = {"changelog.txt", "перелив дк.txt", "Сборная солянка.txt", "UsersUserAppDataLocalTempjmclog_test.txt",
        "стаф18", "доп_атака", "start1", "start2"}
PROMPT = re.compile(r"^\d+H \d+M \d+V .*>\s*$")
EXITS = re.compile(r"^\[ Exits: ?(.*)\]")
KILL = re.compile(r"^(.+?) мертв[аоы]?\. R\.I\.P\.")
EXP = re.compile(r"^Вы получили (\d+) единиц")
LEVEL = re.compile(r"^Вы .*?, (.+?) (\d+) уровня\.")
MAPCH = set("+|:-~^@%$_ ]M[RmGO\"vV<>=#*.!")
FAIL = re.compile(r"Попробуйте сначала открыть|Вы не можете идти|Вам мешает|закрыта|не пускает")
MOVES = {"север", "юг", "восток", "запад", "вверх", "вниз", "с", "ю", "в", "з", "св", "сз", "юв", "юз", "вв", "вн"}


def is_map(l):
    return bool(l) and all(ch in MAPCH or ch in "mMRGO@" for ch in l.strip()) and any(ch in "+|:" for ch in l)


def parse(path):
    lines = [l.rstrip("\r") for l in open(path, encoding="cp1251", errors="replace").read().split("\n")]
    cmds, kills, rooms, level, failed = [], [], OrderedDict(), None, set()
    room, exits, block, after_prompt, last_kill, just_cmd = "?", "", [], False, None, False
    for l in lines:
        s = l.strip()
        if PROMPT.match(s):
            after_prompt = True
            block = []
            continue
        if not s:
            continue
        m = LEVEL.match(s)
        if m and level is None:
            level = (m.group(1), int(m.group(2)))
        if after_prompt:
            after_prompt = False
            if (s[0].islower() or s[0].isdigit()) and len(s) <= 60 and not is_map(s):
                cmds.append((s, room))
                just_cmd = True
                block = []
                continue
        if is_map(s):
            block = []                       # название комнаты идёт сразу после карты
            continue
        if cmds and s == cmds[-1][0] and just_cmd:
            continue                         # повторное эхо любой команды (JMC печатает её дважды)
        if s in MOVES:                       # эхо команды движения, набранной до показа комнаты (JMC печатает его дважды)
            if not (cmds and cmds[-1][0] == s and just_cmd):
                cmds.append((s, room))
                just_cmd = True
            block = []
            continue
        just_cmd = False
        if FAIL.search(s) and cmds and cmds[-1][0] in MOVES:
            failed.add(len(cmds) - 1)
        m = EXITS.match(s)
        if m:
            name = block[0] if block else room
            room, exits = name, m.group(1).strip()
            rooms.setdefault(room, {"exits": exits, "lines": []})
            block = []
            continue
        block.append(s)
        if room in rooms:
            if s not in rooms[room]["lines"] and len(rooms[room]["lines"]) < 40:
                rooms[room]["lines"].append(s)
        m = KILL.match(s)
        if m:
            last_kill = [m.group(1), room, 0, len(cmds)]
            kills.append(last_kill)
            continue
        m = EXP.match(s)
        if m and last_kill and last_kill[2] == 0:
            last_kill[2] = int(m.group(1))
    return level, cmds, kills, rooms, failed


DIRS = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
KEEP = ("область создать", "обл")
# служебные команды пользователя: бой, осмотр, лут, расходники, двери (двери делают триггеры бота), гильдия
SKIP_PREFIX = ("убить", "яр ", "сч", "э", "смотреть", "очистить", "взя", "у ", "а", "осуш", "уч", "ум", "ору", "отпер",
               "откр", "кз", "кс", "инв", "пом", "вст", "огл", "отд", "лег", "гг ", "г ", "экип", "од", "сн", "полож",
               "полез", "лев", "реж", "аф", "где", "зон", "справ", "?", "пить", "есть", "съесть", "закрыть", "запер")


def make_route(cmds, kills, failed=()):
    """Маршрут в формате replay.py из команд лога: движение (комната прихода = комната следующей команды), убийства
    между движениями, область. Двери, лут, ярость и осмотр делают триггеры/бот, в маршрут не входят."""
    steps, pos_kills = [], {}
    anchors = [j for j, (c, _) in enumerate(cmds) if (c in MOVES and j not in failed) or c.startswith(KEEP[0])]
    for n, r, e, ci in kills:                 # убийство относим к последнему состоявшемуся движению перед ним
        prev = [j for j in anchors if j < ci]
        pos_kills.setdefault((prev[-1] if prev else -1) + 1, []).append(n)
    for i, (c, r) in enumerate(cmds):
        nxt_room = cmds[i + 1][1] if i + 1 < len(cmds) else r
        if not nxt_room[:1].isupper() and not nxt_room.startswith("*"):
            nxt_room = "* скрытая деталь *"      # название не распознано (эхо команды/хвост описания): replay верит MSDP
        if c in MOVES:
            if i in failed:
                continue                      # закрытая дверь/«не можете идти»: движение не состоялось
            steps.append({"move": DIRS.get(c, c), "room": nxt_room})
        elif c.startswith(KEEP[0]) or not c.startswith(SKIP_PREFIX):
            steps.append({"cmd": c})          # область и «игровые» команды зоны (повернуть, нажать, дать...)
        names = pos_kills.get(i + 1)
        if names and (c in MOVES or c.startswith(KEEP[0]) or c.startswith("убить")):
            steps.append({"kill": names, "room": nxt_room})
    # убийства в самой первой комнате лога (до первой команды) и повторы: оставляем как есть
    out = []
    for st in steps:                          # подряд идущие kill склеиваем
        if out and "kill" in st and "kill" in out[-1]:
            out[-1]["kill"] += st["kill"]
        else:
            out.append(st)
    return out


def desc_for(name, rooms):
    stem = name.lower()[:5]
    for r in rooms.values():
        for l in r["lines"]:
            if stem in l.lower() and l != name and not l.endswith("мертв. R.I.P."):
                return l + " "
    return ""


def prep(name, db):
    level, cmds, kills, rooms, failed = parse(os.path.join(JMC, name))
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    cnt = Counter(k[0] for k in kills)
    exp = {}
    for n, r, e, _ in kills:
        exp.setdefault(n, []).append(e)
    first_room = {}
    for n, r, e, _ in kills:
        first_room.setdefault(n, r)
    import json
    with open(os.path.join(d, name + "_route.json"), "w", encoding="utf-8") as f:
        json.dump({"start": None, "steps": make_route(cmds, kills, failed)}, f, ensure_ascii=False, indent=0)
    special = [(c, r) for c, r in cmds if c.split()[0] not in MOVES and not re.fullmatch(r"\d*[nsewud]+", c)]
    with open(os.path.join(d, name + "_cmds.txt"), "w", encoding="utf-8") as f:
        for c, r in cmds:
            f.write(f"{c}\t# {r}\n")
    with open(os.path.join(d, name + ".md"), "w", encoding="utf-8") as f:
        f.write(f"# {name} (из лога JMC\\{name})\n\n")
        f.write(f"- персонаж в начале лога: {level[0]} {level[1]} лвл\n" if level else "- уровень в логе не найден\n")
        f.write(f"- команд: {len(cmds)}, комнат: {len(rooms)}, убийств: {len(kills)}, видов мобов: {len(cnt)}\n")
        f.write("- vnum клеток в логе нет (JMC): привязка по MSDP при разведке; V-маршрут собирается после прогона\n\n")
        f.write("## Мобы (убито, средний опыт, где впервые)\n\n| моб | убито | опыт | комната |\n|---|---|---|---|\n")
        for n, c in cnt.most_common():
            e = [x for x in exp[n] if x]
            f.write(f"| {n} | {c} | {sum(e)//len(e) if e else '?'} | {first_room[n]} |\n")
        f.write("\n## Особые команды (не движение)\n\n")
        for c, r in special:
            f.write(f"- `{c}` — {r}\n")
        f.write("\n## Комнаты (порядок первого появления)\n\n")
        for r, v in rooms.items():
            f.write(f"- {r} [{v['exits']}]\n")
    cur = db.cursor()
    with open(os.path.join(d, name + "_mob.csv"), "w", encoding="cp1251", errors="replace", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        w.writerow(["Имя моба", "Описание в комнате", "Hp", "MaxHp", "Mp", "MaxMp", "Опыт", "Деньги", "Уровень",
                    "Агрессивность", "Ассистит?", "Умения", "Профессия", "Раса", "Флаги NPC"])
        for n in cnt:
            row = cur.execute("select level,prof,hp,mana from mob_cards where name=? limit 1", (n,)).fetchone()
            lv, prof, hp, mp = row if row else ("", "", "", "")
            e = [x for x in exp[n] if x]
            w.writerow([n, desc_for(n, rooms), hp, hp, mp, mp, sum(e) // len(e) if e else 0, 0, lv, "false", "false", "",
                        prof or "", "", ""])
    return name, level, len(cmds), len(rooms), len(kills), len(cnt)


def main():
    names = sys.argv[1:] or [n for n in sorted(os.listdir(JMC)) if n not in SKIP and "." not in n]
    db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
    for n in names:
        try:
            print(*prep(n, db), sep="\t")
        except Exception as e:
            print(n, "ОШИБКА", e)


if __name__ == "__main__":
    main()
