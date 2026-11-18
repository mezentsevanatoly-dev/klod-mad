# -*- coding: utf-8 -*-
"""Команда в игру через клиент МАД ГРАФИКА и ответ игры.

python -X utf8 play.py [Айлина|Кимпи] "команда1;команда2" [сек ожидания, по умолчанию 2]
Печатает новые строки игры и итог: клетка (MSDP), хп/мана/энергия.
"""
import json
import sys
import time
import urllib.request

def find_port(name=None):
    """Окно приложения с этим профилем (порты 8765..8774); без имени — первое открытое."""
    for p in range(8765, 8775):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/info", timeout=0.5) as r:
                n = json.loads(r.read().decode("utf-8")).get("name") or ""
        except Exception:
            continue
        if not name or n.lower() == name.lower():
            return p
    return 8765


NAMES = {"айлина", "кимпи"}
if len(sys.argv) > 1 and sys.argv[1].lower() in NAMES:
    BASE = f"http://127.0.0.1:{find_port(sys.argv.pop(1))}"
else:
    BASE = f"http://127.0.0.1:{find_port()}"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    cmds = sys.argv[1] if len(sys.argv) > 1 else ""
    wait = float(sys.argv[2]) if len(sys.argv) > 2 else 2
    start = get("/log")["next"]
    body = "\n".join(c.strip() for c in cmds.split(";")) if cmds.strip() else ""
    urllib.request.urlopen(urllib.request.Request(BASE + "/send", data=body.encode("utf-8"), method="POST"), timeout=5)
    time.sleep(wait)
    lg = get(f"/log?from={start}")
    for ln in lg["lines"]:
        if ln.strip():
            print(ln)
    if lg["partial"].strip():
        import re
        print(re.sub(r"\x1b\[[0-9;]*m", "", lg["partial"]))
    s = get("/api/state")
    c, st = s.get("cur") or {}, s.get("st") or {}
    print(f"== клетка {c.get('vnum')} {c.get('area')} / {c.get('name')} выходы {c.get('exits')} | "
          f"{st.get('hp')}/{st.get('hpm')}H {st.get('mp')}/{st.get('mpm')}M {st.get('mv')}/{st.get('mvm')}V | мобы на карте {s.get('mobs')}")


if __name__ == "__main__":
    main()
