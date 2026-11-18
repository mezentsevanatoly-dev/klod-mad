"""Базовые спидволки города: от комнаты-хаба (портал Аватары) до каждой ключевой комнаты и обратно.

  python tools/city_routes.py "<Город>" [--verify]
Стоять нужно в хабе (портал Аватары города). Берёт `путь список`, для каждой комнаты `путь маршрут <комната>` (печатает шаги
«з з с в вв…»), переводит в спидволк (`2wn3e`), строит обратный, пишет в speedwalks.txt и таблицу speedwalks (game.db),
таблицу routes (город, откуда, куда, путь, обратный, шагов, проверен). --verify: идёт по спидволку, сверяет название комнаты, возвращается.
Двери и закрытые проходы `путь маршрут` не учитывает: такие маршруты помечаются непроверенными.
"""
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
TOK = {"с": "n", "ю": "s", "в": "e", "з": "w", "вв": "u", "вн": "d"}
INV = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"}


def cmd(cmds, wait=2.0):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py")] + [f"{c}|{wait}" for c in cmds],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    return r.stdout


def cur(out):
    m = re.findall(r"\[cur\] \{'vnum': '(\d+)', 'area': '([^']*)', 'name': '([^']*)'", out.replace("\n", " "))
    return m[-1] if m else ("", "", "")


def compress(letters):
    out, i = "", 0
    while i < len(letters):
        j = i
        while j < len(letters) and letters[j] == letters[i]:
            j += 1
        out += (str(j - i) if j - i > 1 else "") + letters[i]
        i = j
    return out


def key_rooms():
    out = cmd(["путь список"], 3)
    rooms = []
    for l in out.split("\n"):
        if l.startswith(" ") and not l.startswith("Список") and l.strip():
            name = re.sub(r"\s*\([^)]*\)\s*$", "", l.strip())
            if name:
                rooms.append(name)
    return rooms


def main(city, verify):
    hub = cur(cmd(["где"], 2))
    if not hub[0]:
        sys.exit("не вижу комнату")
    print(f"хаб: {hub[0]} {hub[2]} ({hub[1]})")
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS routes (city TEXT, hub_vnum TEXT, to_name TEXT, path TEXT, back TEXT, steps INTEGER,
                 verified TEXT, PRIMARY KEY (city, hub_vnum, to_name))""")
    sw = open(os.path.join(HERE, "speedwalks.txt"), "a", encoding="utf-8")
    sw.write(f"# {city}: от хаба {hub[0]} ({hub[2]}) к ключевым комнатам и обратно (tools/city_routes.py)\n")
    n = 0
    for room in key_rooms():
        out = cmd([f"путь маршрут {room}"], 2.5)
        m = re.search(r"Путь к комнате \"[^\"]*\":\s*(.+)", out)
        if not m:
            print(f"  {room}: маршрут не получен")
            continue
        toks = m.group(1).strip().split()
        if not toks or any(t not in TOK for t in toks):
            print(f"  {room}: непонятные шаги {toks[:6]}")
            continue
        letters = [TOK[t] for t in toks]
        path = compress(letters)
        back = compress([INV[x] for x in reversed(letters)])
        ver = ""
        if verify:
            o = cmd([f"!sw {path}"], 6)
            vnum, area, name = cur(o)
            ok_name = name.lower().startswith(room.lower()[:6]) or room.lower().startswith(name.lower()[:6])
            o2 = cmd([f"!sw {back}"], 6)
            home = cur(o2)[0] == hub[0]
            ver = ("ok" if ok_name else f"название «{name}»") + ("" if home else "; НЕ вернулась в хаб")
            if not home:
                print(f"  {room}: не вернулась в хаб ({cur(o2)}); останавливаюсь")
                break
        key = re.sub(r"[\s\":]+", "_", room).strip("_")
        sw.write(f"{city}:{key} = {path}\n{city}:{key}_обратно = {back}\n")
        c.execute("INSERT INTO speedwalks VALUES (?,?,?,?)", (f"{city}:{key}", path, "", f"хаб {hub[0]} -> {room}"))
        c.execute("INSERT INTO speedwalks VALUES (?,?,?,?)", (f"{city}:{key}_обратно", back, hub[0], f"{room} -> хаб"))
        c.execute("INSERT OR REPLACE INTO routes VALUES (?,?,?,?,?,?,?)", (city, hub[0], room, path, back, len(letters), ver or "не проверен"))
        c.commit()
        n += 1
        print(f"  {room}: {path}  ({len(letters)} шагов) {ver}")
    sw.close()
    print(f"маршрутов записано: {n}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], "--verify" in sys.argv)
