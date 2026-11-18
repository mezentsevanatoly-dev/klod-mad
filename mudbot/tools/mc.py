"""mc — мои команды в игру через демон mudd (tools/mudd.py).

python tools/mc.py "смотреть" "север|2" "убить моб|until=мертв|max=40"   -> ответы игры по пакету
python tools/mc.py -s "ск имя привет; север"                              -> «;» разделяет команды
python tools/mc.py status                                                 -> соединение, вход, тревога, HP/MP/MV, комната (MSDP)
python tools/mc.py tail [N]                                               -> последние N строк
python tools/mc.py read [сек]                                             -> новое с прошлого вызова (ждать сек)

У команды после «|» можно: число (тишина, сек), until=регулярка (ждать строку), max=сек (потолок).
Ответ — строки игры после пакета; промпты вида «298H 125M…» прячутся (MC_RAW=1 — показать всё).
Порт демона: MUDD_API (по умолчанию 5599).
"""
import json
import os
import re
import socket
import sys

PORT = int(os.environ.get("MUDD_API", 5599))
POS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".mc_pos")
PROMPT = re.compile(r"^\d+H \d+M \d+V ")


def call(req):
    try:
        s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    except OSError:
        sys.exit(f"демон mudd не запущен (порт {PORT}): запустите tools/mudd.py в отдельном окне")
    s.settimeout(300)
    s.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))
    data = b""
    while not data.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return json.loads(data.decode("utf-8"))


def show(lines):
    raw = os.environ.get("MC_RAW") == "1"
    for l in lines:
        if raw or (l.strip() and not PROMPT.match(l)):
            print(l)


def save_pos(seq):
    try:
        open(POS, "w").write(str(seq))
    except OSError:
        pass


def parse_cmd(arg):
    """«команда|2|until=рег|max=40» -> (команда, quiet, until, max)."""
    parts = arg.split("|")
    cmd, quiet, until, mx = parts[0], None, None, None
    for p in parts[1:]:
        if p.startswith("until="):
            until = p[6:]
        elif p.startswith("max="):
            mx = float(p[4:])
        else:
            quiet = float(p)
    return cmd, quiet, until, mx


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "status":
        r = call({"op": "status"})
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if argv[0] == "tail":
        r = call({"op": "tail", "n": int(argv[1]) if len(argv) > 1 else 40})
        show(r["lines"])
        save_pos(r["seq"])
        return 0
    if argv[0] == "read":
        try:
            since = int(open(POS).read())
        except (OSError, ValueError):
            since = 0
        r = call({"op": "read", "since": since, "quiet": 0.5, "max": float(argv[1]) if len(argv) > 1 else 0.5})
        show(r["lines"])
        save_pos(r["seq"])
        return 0
    args = argv
    if args[0] == "-s":                               # одна строка с «;»
        args = [p.strip() for p in " ".join(args[1:]).split(";") if p.strip()]
    quiet, until, mx, cmds = 1.0, None, 30.0, []
    for a in args:
        c, q, u, m = parse_cmd(a)
        quiet = max(quiet, q or 0)
        until = u or until
        mx = m or mx
        cmds.append(c)
    r = call({"op": "send", "cmds": cmds, "quiet": quiet, "until": until, "max": mx})
    if not r["ok"]:
        print("ОШИБКА:", r["error"])
        return 2
    show(r["lines"])
    save_pos(r["seq"])
    st = r["state"]["prompt"]
    if st:
        print(f"[hp {st['hp']} mp {st['mp']} mv {st['mv']}{' БОЙ ' + st['foe'] if st['in_battle'] else ''}]")
    if r["state"]["alarm"]:
        print("!!! ТРЕВОГА проверки присутствия — отвечает человек")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
