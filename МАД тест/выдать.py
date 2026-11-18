# -*- coding: utf-8 -*-
"""Тадия (бог) создаёт предметы и отдаёт персонажу: python выдать.py <аккаунт> <персонаж> "предмет1" "предмет2" ...
Персонаж входит в игру, Тадия приходит к нему в комнату, создаёт и передаёт, персонаж надевает (команда «одеть все»).
Только ЛОКАЛЬНЫЙ сервер."""
import os
import re
import socket
import sys
import time

PW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "пароль_тест.txt"), encoding="utf8").read().strip()


class S:
    def __init__(self, acc):
        self.s = socket.create_connection(("127.0.0.1", 5555), timeout=5)
        self.rd(1.5)
        self.say("1")
        self.say(acc)
        self.say(PW)

    def rd(self, w=1.0):
        self.s.settimeout(w)
        b, end = b"", time.time() + w
        while time.time() < end:
            try:
                c = self.s.recv(8192)
                if not c:
                    break
                b += c
                end = time.time() + 0.4
            except socket.timeout:
                break
        t = b.decode("cp1251", "replace").replace("яя", "я")
        return re.sub(r"\x1b\[[0-9;]*m|\[[0-9;]*m", "", t)

    def say(self, c, w=1.0):
        self.s.sendall(c.encode("cp1251").replace(bytes([255]), bytes([255, 255])) + b"\r\n")
        return self.rd(w)


acc, name, items = sys.argv[1], sys.argv[2], sys.argv[3:]
ch = S(acc)
ch.say("1")                       # меню: «Войти в игру»
ch.say("к")                       # закрыть возможный пейджер
god = S("Тестер")
god.say("")                       # Тадия уже в игре (меню пропускается при восстановлении связи)
where = ch.say("где") or ""
god.say("админ комната 100001")   # приёмная гостиницы Элендора — стартовая клетка
for it in items:
    r = god.say("админ предметы создать " + it)
    r += god.say("дать %s %s" % (it.split()[0], name))
    print(it, "->", r.strip().replace("\r\n", " | ")[:160])
print(ch.say("одеть все", 1.5))
print(ch.say("экип", 1.5))
