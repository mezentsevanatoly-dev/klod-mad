# -*- coding: utf-8 -*-
"""Поиск строк по ключевым словам в Sow.exe / Kernel.dll."""
import re
import sys

KEYS = sys.argv[1:] or ["port", "Startup", "Server", "socket", "Socket", "listen",
                        "maxClients", "Sow.ini", "ini", "bind", "Client"]


def strings(path, minlen=4):
    d = open(path, "rb").read()
    return [m.group().decode("cp1251", "replace")
            for m in re.finditer(rb"[\x20-\x7e\xa8-\xff]{%d,}" % minlen, d)]


def main():
    base = r"C:\Users\User\Desktop\Клод мад\МАД ГРАФИКА\sow_server"
    for f in ("Sow.exe", "Kernel.dll"):
        print("=" * 70)
        print(f)
        print("=" * 70)
        for s in strings(base + "\\" + f):
            if any(k in s for k in KEYS) and len(s) < 200:
                print(repr(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
