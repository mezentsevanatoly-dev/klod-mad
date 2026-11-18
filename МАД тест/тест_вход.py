# -*- coding: utf-8 -*-
"""Диалог с ЛОКАЛЬНЫМ сервером: python тест_вход.py ответ1 ответ2 ... (печатает ответы сервера). Пароль подставляется как {PW}."""
import os
import socket
import sys
import time

PW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "пароль_тест.txt"), encoding="utf8").read().strip()
s = socket.create_connection(("127.0.0.1", 5555), timeout=5)


def rd(w=1.2):
    s.settimeout(w)
    b = b""
    end = time.time() + w
    while time.time() < end:
        try:
            c = s.recv(8192)
            if not c:
                break
            b += c
            end = time.time() + 0.5
        except socket.timeout:
            break
    return b.decode("cp1251", "replace")


rd(1.5)
s.sendall(b"1\r\n")
rd(1.5)
for a in sys.argv[1:]:
    # 0xFF (буква «я») в режиме 1 (JMC/Telnet) удваивается, в ответах сервера тоже
    s.sendall(a.replace("{PW}", PW).encode("cp1251").replace(bytes([255]), bytes([255, 255])) + b"\r\n")
    t = rd(1.5).replace("\x1b", "").replace("яя", "я")
    print(">>", "***" if "{PW}" in a else a)
    print(t[-1500:])
