"""Сохранить разделы справки игры в data/help/<тема>.txt (через работающего бота: inbox.txt / out.log).

python tools/dump_help.py маг друид ...     (листает страницы пробелом до конца)
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from explore_zone import FileClient  # noqa: E402
from mudbot.parser import parse_status  # noqa: E402

OUT = os.path.join(ROOT, "data", "help")
PAGER = "[<Enter> - показать следующую страницу"


def fetch(c: FileClient, topic: str, quiet=1.2, maxwait=20, cmd=None) -> str:
    """Справка по теме, или вывод любой команды с листанием (cmd="зоны")."""
    while not c.lines.empty():
        c.lines.get()
    c.send(cmd or "?" + topic)
    lines, last, t0 = [], time.time(), time.time()
    while time.time() - t0 < maxwait:
        try:
            ln = c.lines.get(timeout=0.1)
        except Exception:
            if time.time() - last > quiet and lines:
                break
            continue
        last = time.time()
        if PAGER in ln.text:
            c.send(" ")                 # следующая страница
            continue
        if parse_status(ln.text) or ln.text.startswith("[claude"):
            continue
        lines.append(ln.text)
    return "\n".join(lines).strip()


def main(topics):
    os.makedirs(OUT, exist_ok=True)
    c = FileClient()
    for t in topics:
        txt = fetch(c, t)
        fn = os.path.join(OUT, re.sub(r"[^\w]+", "_", t) + ".txt")
        open(fn, "w", encoding="utf-8").write(txt)
        print(f"{t}: {len(txt.splitlines())} строк")


if __name__ == "__main__":
    main(sys.argv[1:])
