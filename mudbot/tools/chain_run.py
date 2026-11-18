"""Цепочки поездок: шаги «спидволк» и «команда» подряд, одной командой. Хранятся в data/game.db (таблица chains).

  python tools/chain_run.py add <имя> "<описание>" "!sw А" "купить 11" "купить 12" "!sw А_обратно"
  python tools/chain_run.py list
  python tools/chain_run.py show <имя>
  python tools/chain_run.py run <имя> [--dry]     --dry только печатает шаги

Шаг начинается с `!sw ` — спидволк из speedwalks.txt/базы (по имени), иначе — обычная команда игры.
Покупка без согласия не делается: цепочки с покупками запускать только по просьбе пользователя.
"""
import os
import sqlite3
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")


def conn():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS chains (name TEXT PRIMARY KEY, descr TEXT, steps TEXT, updated TEXT)")
    return c


def send(step, wait):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py"), f"{step}|{wait}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    return r.stdout


def main(a):
    c = conn()
    if not a or a[0] == "list":
        for n, d, s, u in c.execute("SELECT name, descr, steps, updated FROM chains ORDER BY name"):
            print(f"{n}: {d} ({len(s.split(chr(10)))} шагов)")
    elif a[0] == "add":
        name, descr, steps = a[1], a[2], a[3:]
        c.execute("INSERT OR REPLACE INTO chains VALUES (?,?,?,?)", (name, descr, "\n".join(steps), time.strftime("%d.%m %H:%M")))
        c.commit()
        print("записана цепочка", name, "-", len(steps), "шагов")
    elif a[0] == "show":
        r = c.execute("SELECT descr, steps FROM chains WHERE name=?", (a[1],)).fetchone()
        print(r[0]);  print(r[1])
    elif a[0] == "run":
        r = c.execute("SELECT descr, steps FROM chains WHERE name=?", (a[1],)).fetchone()
        if not r:
            sys.exit("нет такой цепочки")
        for i, step in enumerate(r[1].split("\n"), 1):
            print(f"{i}. {step}", flush=True)
            if "--dry" in a:
                continue
            out = send(step, 45 if step.startswith("!sw") else 2)
            if "не дошли" in out or "нет пути" in out.lower():
                sys.exit(f"сбой на шаге {i}: {step}")
        print("цепочка выполнена")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
