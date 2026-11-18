"""Поиск комнаты по названию обходом в глубину по MSDP-выходам: python -X utf8 tools/find_room.py <старт_vnum> "<название>" [лимит_комнат]
Идём по всем невиденным выходам (города и зоны из BAN не заходим), возвращаемся назад обратным ходом, останавливаемся на первой
комнате с таким названием. Лог ходов: tools/find_room.log. Ничего не бьёт сам (бой — встроенные триггеры/авто бота).
"""
import ast
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(os.environ, MUD_VIA="bot")
BAN = ("Город", "Болото", "Порт", "Парк")
import sqlite3
KNOWN = {str(v) for v, in sqlite3.connect(os.path.join(ROOT, "data", "game.db")).execute("select vnum from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
BACK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
UNKNOWN_ONLY = "--new" in sys.argv
LOG = open(os.path.join(ROOT, "tools", "find_room.log"), "a", encoding="utf-8")


def cmd(c):
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tools", "cmd.py"), c], env=ENV, cwd=ROOT,
                       capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    m = re.findall(r"^\[cur\] (\{.*\})\s*$", r.stdout, re.M)
    return ast.literal_eval(m[-1]) if m else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    start, target = args[0], args[1]
    limit = int(args[2]) if len(args) > 2 else 120
    start_list = start.split(",")
    cur = cmd(f"!go {start_list[0]}")
    seen, stack, n = {cur["vnum"]}, [], 0
    names = {}

    def say(s):
        LOG.write(s + "\n")
        LOG.flush()
        print(s, flush=True)

    def dfs(c):
        nonlocal n
        for d, t in list(c["exits"].items()):
            t = str(t)
            if t in seen or (UNKNOWN_ONLY and t in KNOWN):     # только клетки, которых нет в нашей базе rooms (новые)
                continue
            seen.add(t)
            nc = cmd(RU[d])
            if not nc or nc["vnum"] != t:
                say(f"ход {d} из {c['vnum']} не привёл в {t} ({nc and nc['vnum']}): пропуск")
                if nc and nc["vnum"] != c["vnum"]:
                    cmd(RU[BACK[d]])
                continue
            n += 1
            say(f"{n}: {nc['vnum']} {nc['area']} | {nc['name']}")
            if nc["name"] == target:
                say("НАШЛА " + str(nc))
                return True
            if n >= limit:
                return True
            if not any(b in nc["area"] for b in BAN):
                if dfs(nc):
                    return True
            back = cmd(RU[BACK[d]])
            if not back or back["vnum"] != c["vnum"]:
                say(f"обратный ход из {t} не привёл в {c['vnum']}: возвращаюсь через !go")
                back = cmd(f"!go {c['vnum']}")
                if not back or back["vnum"] != c["vnum"]:
                    say("потерялась, стоп")
                    return True
        return False

    if dfs(cur):
        return
    for s in start_list[1:]:                      # несколько стартов по дороге: seen общий
        cur = cmd(f"!go {s}")
        if cur and dfs(cur):
            return


if __name__ == "__main__":
    main()
