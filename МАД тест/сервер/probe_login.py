# -*- coding: utf-8 -*-
"""Пошаговый разбор рукопожатия тестового сервера на 127.0.0.1:5555.

Показывает, что сервер отвечает после каждого шага (кодировка, вход,
создание персонажа), ничего не меняя в клиенте.
"""
import socket
import time

HOST, PORT = "127.0.0.1", 5555


def drain(s, wait=1.2, label=""):
    s.settimeout(wait)
    buf = b""
    end = time.time() + wait
    while time.time() < end:
        try:
            chunk = s.recv(8192)
        except socket.timeout:
            break
        if not chunk:
            print("[%s] соединение закрыто сервером" % label)
            break
        buf += chunk
        end = time.time() + 0.4
    text = buf.decode("cp1251", "replace")
    print("---- после: %s ----" % label)
    for line in text.splitlines():
        print("  | " + line)
    if not buf:
        print("  | (тишина)")
    return buf


def main():
    s = socket.create_connection((HOST, PORT), timeout=5)
    drain(s, 1.5, "подключение")

    for step, payload in enumerate([b"1\r\n"], 1):
        s.sendall(payload)
        drain(s, 1.5, "отправлено %r" % payload.strip())

    for cmd in ["гость\r\n", "тест\r\n"]:
        s.sendall(cmd.encode("cp1251"))
        drain(s, 1.5, "отправлено %r" % cmd.strip())

    s.close()


if __name__ == "__main__":
    main()
