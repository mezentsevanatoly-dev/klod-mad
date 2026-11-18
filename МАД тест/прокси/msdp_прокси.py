# -*- coding: utf-8 -*-
"""MSDP-прокси для ЛОКАЛЬНОГО сервера Sow.exe (он MSDP не отдаёт, а клиент и бот ходят по номерам клеток).

    клиент --(127.0.0.1:5556)--> прокси --(127.0.0.1:5555)--> Sow.exe
    python -X utf8 msdp_прокси.py [порт_прокси=5556]      клиент запускать с --game-port 5556

Всё, что идёт между клиентом и сервером, пересылается как есть. Дополнительно прокси читает текст игры, находит
комнату (название + выходы из строки «Вых:СВЮЗ>») среди клеток game.db и шлёт клиенту MSDP ROOM {VNUM, AREA, NAME, EXITS}.
shortcut: номер клетки — по названию и выходам (если таких клеток в game.db несколько — берётся соседняя с прежней),
клетки, которых нет в game.db, номера не получат; когда зоны на стенде будут свои — можно брать номер из самой зоны.
"""
import json
import os
import re
import socket
import sqlite3
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), "клиент", "data", "game.db")
LOG = os.path.join(HERE, "прокси.log")
LISTEN = int(sys.argv[1]) if len(sys.argv) > 1 else 5556
UP = ("127.0.0.1", 5555)
IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
MSDP = 69
ANSI = re.compile(r"\x1b\[[0-9;]*m")
PROMPT = re.compile(r"\d+H \d+M \d+V \d+X \d+C Вых:([^>\n]*)>")
EXITS = {"С": "N", "В": "E", "Ю": "S", "З": "W", "v": "D", "^": "U"}


def norm(s):
    return s.strip().lower().replace("ё", "е")


def log(*a):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")


def load_rooms():
    by = {}
    c = sqlite3.connect(DB)
    for vnum, zone, name, ex in c.execute("select vnum,zone,name,exits from rooms"):
        try:
            ex = json.loads(ex or "{}")
        except ValueError:
            ex = {}
        by.setdefault(norm(name), []).append((str(vnum), zone or "", name, ex))
    c.close()
    return by


ROOMS = load_rooms()
BYV = {r[0]: r for v in ROOMS.values() for r in v}
DIRS = {"север": "N", "с": "N", "юг": "S", "ю": "S", "восток": "E", "в": "E", "запад": "W", "з": "W",
        "вверх": "U", "вв": "U", "вниз": "D", "вн": "D"}


def load_zones():
    """Зоны, реально загруженные на стенде (`сервер\\db\\Zones.txt`): номер клетки = зона*1000 + комната."""
    p = os.path.join(os.path.dirname(HERE), "сервер", "db", "Zones.txt")
    z = set()
    try:
        for ln in open(p, encoding="cp1251"):
            w = ln.split()
            if w and w[0].isdigit():
                z.add(int(w[0]))
    except OSError as e:
        log("Zones.txt не прочитан:", e)
    return z


ZONES = load_zones()
LAST_ZONE = ""                                       # зона последней опознанной клетки
LIVE_ZONES = {}                                      # cid -> зона, где стоит это окно сейчас


def known(n):
    """Есть точное название или оно — начало названия из game.db (стенд 2017 короче)."""
    return n in ROOMS or any(k.startswith(n) for k in ROOMS)


def dist(a, b, maxd=8):
    """Короткий путь по выходам game.db: при споре одинаковых названий берём ближнюю к прежней клетке."""
    a, b = str(a), str(b)
    if a == b:
        return 0
    seen, frontier = {a}, [a]
    for d in range(1, maxd + 1):
        nxt = []
        for v in frontier:
            r = BYV.get(v)
            if not r:
                continue
            for w in r[3].values():
                w = str(w)
                if w == b:
                    return d
                if w not in seen:
                    seen.add(w)
                    nxt.append(w)
        frontier = nxt
        if not frontier:
            break
    return 99


def locate(name, exits, cur, hint=None, cid=None):
    key = norm(name)
    c = ROOMS.get(key, [])
    if not c:                                        # на стенде название короче: «Маленькая доска» вместо «… объявлений»
        c = [r for k, lst in ROOMS.items() if k.startswith(key) for r in lst]
    f = [r for r in c if set(r[3]) == exits]
    c = f or c
    if ZONES:                                      # только клетки зон, которые есть на стенде (502021 «Мория» и т. п. отпадают)
        stand = [r for r in c if int(r[0]) // 1000 in ZONES]
        if stand:
            c = stand
    if not cur:                                    # вход в игру: если имя неоднозначно — зона, где стоит второе окно
        zs = {z for k, z in LIVE_ZONES.items() if k != cid}
        same = [r for r in c if r[1] in zs] if zs else []
        if not same and LAST_ZONE:
            same = [r for r in c if r[1] == LAST_ZONE]
        if same:
            c = same
    if hint and (not c or hint in c):
        return hint
    if len(c) > 1 and cur:
        near = [r for r in c if r[0] in set(cur[3].values())]   # соседняя с прежней
        if not near:                                            # не соседняя — ближайшая по карте
            ds = [(dist(cur[0], r[0]), r) for r in c]
            best = min(d for d, _ in ds)
            if best <= 6:
                near = [r for d, r in ds if d == best]
        if not near and set(cur[3]) == exits:                   # та же комната: выходы совпали
            near = [r for r in c if r[0] == cur[0]]
        c = near or c
    return c[0] if c else None


def msdp_room(r):
    def kv(k, v):
        return bytes([1]) + k.encode() + bytes([2]) + v
    ex = b"".join(kv(d, str(v).encode()) for d, v in r[3].items())
    body = bytes([1]) + b"ROOM" + bytes([2, 3]) + kv("VNUM", r[0].encode()) + kv("AREA", r[1].encode("cp1251", "replace")) \
        + kv("NAME", r[2].encode("cp1251", "replace")) + bytes([1]) + b"EXITS" + bytes([2, 3]) + ex + bytes([4, 4])
    return bytes([IAC, SB, MSDP]) + body.replace(bytes([255]), bytes([255, 255])) + bytes([IAC, SE])


def strip_iac(data, pend):
    """-> (текст игры, остаток). Двойной 0xFF — буква «я»; команды и подпереговоры выбрасываются."""
    data = pend + data
    out, i = bytearray(), 0
    while i < len(data):
        b = data[i]
        if b != IAC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= len(data):
            return bytes(out), data[i:]
        n = data[i + 1]
        if n == IAC:
            out.append(255)
            i += 2
        elif n == SB:
            j = data.find(bytes([IAC, SE]), i)
            if j < 0:
                return bytes(out), data[i:]
            i = j + 2
        elif n in (DO, DONT, WILL, WONT):
            if i + 2 >= len(data):
                return bytes(out), data[i:]
            i += 3
        else:
            i += 2
    return bytes(out), b""


class Session:
    def __init__(self, cs, cid=0):
        self.cs = cs
        self.cid = cid
        self.seen_unknown = set()
        self.us = socket.create_connection(UP, timeout=10)
        self.us.settimeout(None)
        self.cur = None
        self.buf = ""
        self.pend = b""
        self.logged_raw = False
        self.lock = threading.Lock()
        self.msdp = False
        self.last_dir = None

    def to_client(self, b):
        with self.lock:
            try:
                self.cs.sendall(b)
            except OSError:
                pass

    def send_room(self):
        if self.cur:
            self.to_client(msdp_room(self.cur))

    def feed(self, raw):
        global LAST_ZONE
        txt, self.pend = strip_iac(raw, self.pend)
        self.buf += ANSI.sub("", txt.decode("cp1251", "replace")).replace("\r", "")
        while True:
            m = PROMPT.search(self.buf)
            if not m:
                break
            seg, self.buf = self.buf[:m.start()], self.buf[m.end():]
            exits = {EXITS[ch] for ch in m.group(1) if ch in EXITS}
            lines = seg.lstrip(" ").split("\n")      # после прежнего приглашения «Вых:..> » название идёт на той же строке
            hint = None
            if self.cur and self.last_dir:                 # куда мы шли: клетка за выходом прежней
                nv = self.cur[3].get(self.last_dir)
                hint = BYV.get(str(nv)) if nv else None
            self.last_dir = None
            r = None
            for ln in lines:                        # название комнаты — строка, совпадающая с названием клетки (в кратком режиме описания нет)
                if ln and not ln.startswith(" ") and known(norm(ln)):
                    r = locate(ln, exits, self.cur, hint, self.cid)
                    break
            if r is None and hint and any(x and not x.startswith(" ") for x in lines[:1]) and lines[0].strip()                     and not known(norm(lines[0])) and len(lines[0]) < 60 and lines[0].strip()[0].isupper():
                r = hint                            # название на стенде с опечаткой — верим направлению шага
            if r is None and lines and self.cid and len(self.seen_unknown) < 40:
                nm = lines[0].strip()
                if 2 < len(nm) < 50 and nm[0].isupper() and not known(norm(nm)) and nm not in self.seen_unknown:
                    self.seen_unknown.add(nm)
                    log("[%d] без клетки:" % self.cid, nm, "".join(sorted(exits)))
            if r:
                if not self.cur or r[0] != self.cur[0]:
                    log("[%d] клетка" % self.cid, r[0], r[2])
                self.cur = r
                LAST_ZONE = r[1]
                LIVE_ZONES[self.cid] = r[1]
                self.send_room()
        if not self.logged_raw and not self.cur and len(self.buf) > 400:
            self.logged_raw = True
            log("[%d] буфер:" % self.cid, repr(self.buf[-180:]))
        self.buf = self.buf[-4000:]

    def run(self):
        self.to_client(bytes([IAC, WILL, MSDP]))
        threading.Thread(target=self.up_down, daemon=True).start()
        pend = b""
        while True:                              # клиент -> сервер, MSDP-запросы клиента не пересылаем
            d = self.cs.recv(8192)
            if not d:
                break
            d = pend + d
            pend, out, i = b"", bytearray(), 0
            while i < len(d):
                if d[i] == IAC and i + 1 < len(d) and d[i + 1] == SB:
                    j = d.find(bytes([IAC, SE]), i)
                    if j < 0:
                        pend = d[i:]
                        break
                    if d[i + 2:i + 3] == bytes([MSDP]):
                        self.msdp = True
                        self.send_room()
                    else:
                        out += d[i:j + 2]
                    i = j + 2
                elif d[i] == IAC and i + 2 < len(d) and d[i + 1] in (DO, DONT, WILL, WONT) and d[i + 2] == MSDP:
                    i += 3
                elif d[i] == IAC and i + 1 >= len(d):
                    pend = d[i:]
                    break
                else:
                    out.append(d[i])
                    i += 1
            if out:
                w = (bytes(out).decode("cp1251", "replace").strip().lower().splitlines() or [""])[-1].strip()
                if w in DIRS:
                    self.last_dir = DIRS[w]
                if os.environ.get("ПРОКСИ_ОТЛАДКА"):
                    log("клиент->сервер", bytes(out)[:120])
                self.us.sendall(bytes(out))

    def up_down(self):
        first = True
        try:
            while True:
                d = self.us.recv(8192)
                if not d:
                    log("[%d] сервер закрыл соединение" % self.cid)
                    break
                if first:
                    first = False
                    log("[%d] первые байты" % self.cid, len(d))
                self.to_client(d)                # сначала клиенту как есть
                try:
                    self.feed(d)                 # потом разбор и, при смене клетки, MSDP ROOM
                except Exception as e:           # разбор не должен убивать сессию
                    log("[%d] ошибка разбора:" % self.cid, repr(e), "байт", len(d))
        except OSError:
            pass
        finally:
            LIVE_ZONES.pop(self.cid, None)
            for s in (self.cs, self.us):
                try:
                    s.close()
                except OSError:
                    pass


def main():
    srv = socket.socket()
    try:
        srv.bind(("127.0.0.1", LISTEN))
    except OSError:
        log("порт", LISTEN, "уже занят — прокси, видимо, запущен")
        return
    srv.listen(8)
    log("прокси слушает", LISTEN, "клеток в game.db:", sum(len(v) for v in ROOMS.values()))
    cid = 0
    while True:
        cs, addr = srv.accept()
        cid += 1
        log("[%d] подключился" % cid, addr[1] if addr else "")
        try:
            threading.Thread(target=Session(cs, cid).run, daemon=True).start()
        except OSError as e:
            log("нет связи с сервером:", e)
            cs.close()


if __name__ == "__main__":
    main()
