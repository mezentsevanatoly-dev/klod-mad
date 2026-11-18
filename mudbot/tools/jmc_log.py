"""Разбор логов JMC: что игрок набирал, где ходил, кого бил.

python tools/jmc_log.py "C:/Users/User/Desktop/ААА/парк"
Команда игрока в логе это строка сразу после строки состояния (prompt). Строки входа (имя и пароль)
пропускаются и никуда не выводятся.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mudbot.parser import RoomParser, parse_event, parse_status  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MOVES = {"север", "юг", "восток", "запад", "вверх", "вниз", "с", "ю", "в", "з", "вв", "вн"}


def parse(path):
    text = open(path, "rb").read().decode("cp1251", errors="replace")
    lines = [ANSI.sub("", l).rstrip("\r") for l in text.split("\n")]
    cmds, rooms, kills, xp = [], [], collections.Counter(), 0
    rp = RoomParser()
    prev_prompt, skip_login = False, 0
    for l in lines:
        s = l.strip()
        if "Введите имя своего пользователя" in s:
            skip_login = 2                       # имя и пароль не берём
            continue
        if skip_login and s and not s.startswith("Пароль"):
            skip_login -= 1
            continue
        if s.startswith("Пароль"):
            continue
        st = parse_status(s)
        if prev_prompt and s and not st and len(s) < 60 and not s.startswith(("[", "Вы ", "Ваш")):
            cmds.append(s)
        r = rp.feed(l)
        if r and r.name:
            rooms.append(r.name)
        ev = parse_event(s)
        if ev and ev[0] == "kill":
            kills[ev[1]["who"]] += 1
        if ev and ev[0] == "xp":
            xp += int(ev[1]["n"])
        prev_prompt = bool(st) or s.endswith(">")
    return cmds, rooms, kills, xp


def main():
    path = sys.argv[1]
    cmds, rooms, kills, xp = parse(path)
    c = collections.Counter(cmds)
    moves = [x for x in cmds if x.split()[0] in MOVES]
    print(f"== {os.path.basename(path)}: команд {len(cmds)}, комнат {len(rooms)} (разных {len(set(rooms))}), "
          f"убийств {sum(kills.values())}, опыта {xp}")
    print("частые команды:", ", ".join(f"{k}×{v}" for k, v in c.most_common(25)))
    print("убиты:", ", ".join(f"{k}×{v}" for k, v in kills.most_common(20)))
    print("комнаты:", ", ".join(f"{k}×{v}" for k, v in collections.Counter(rooms).most_common(15)))
    print("первые 60 команд:", " | ".join(cmds[:60]))


if __name__ == "__main__":
    main()
