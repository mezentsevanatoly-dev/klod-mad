# -*- coding: utf-8 -*-
"""Основа -> тестовые папки (правила: ПРАВИЛА\\УРОВНИ_ТЕСТА.md). В обратную сторону скрипт ничего не копирует.

    python -X utf8 синхрон.py локальный [--личное] [--сухо]     МАД ГРАФИКА -> МАД тест\\клиент  (адрес сервера 127.0.0.1)
    python -X utf8 синхрон.py основы    [--личное] [--сухо]     МАД ГРАФИКА -> МАД тест основы\\клиент  (настоящая игра)
    --сухо   только показать, что изменится.   --личное   ещё профили, аккаунты, карточки мобов, фк.txt (только если файла там нет).

Копируется только то, что новее или отличается: код клиента, data\\ (карта, зоны, мобы), гаги, запускалка.
Личные файлы тестовой папки (аккаунты стенда, логи, его game.db при отличиях по --личное) без --личное не трогаются.
"""
import filecmp
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "МАД ГРАФИКА")
КОД = ["server.py", "index.html", "jmcprofile.py", "гаги.txt", "Погоняем лысого.vbs", "VERSION", "CHANGELOG.md", "README.md", "LICENSE"]
ДАННЫЕ = ["data"]                        # game.db, ЗОНЫ, известные_строки, presence_words
ЛИЧНОЕ = ["карточки_мобов.csv", "фк.txt"]
ЛИЧНОЕ_МАСКИ = (r"профиль_.*\.txt", r"аккаунт_.*\.txt", r"экип_.*\.txt")
ПАТЧ = ('HOST, PORT = "sowmud.ru", 5555',
        'HOST, PORT = "127.0.0.1", 5555   # тестовая копия: только локальный сервер, на боевой попасть нельзя')


def copy(src, dst, сухо):
    if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
        return False
    print(("[сухо] " if сухо else "") + "копирую", os.path.relpath(dst, ROOT))
    if not сухо:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    return True


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a or a[0] not in ("локальный", "основы"):
        sys.exit(__doc__)
    локальный, сухо, личное = a[0] == "локальный", "--сухо" in sys.argv, "--личное" in sys.argv
    dst_root = os.path.join(ROOT, "МАД тест" if локальный else "МАД тест основы", "клиент")
    n = 0
    for f in КОД:
        n += copy(os.path.join(SRC, f), os.path.join(dst_root, f), сухо and True) if f != "server.py" or not локальный else 0
    for d in ДАННЫЕ:
        for r, _, names in os.walk(os.path.join(SRC, d)):
            for f in names:
                if ".bak" in f:
                    continue
                s = os.path.join(r, f)
                n += copy(s, os.path.join(dst_root, os.path.relpath(s, SRC)), сухо)
    if локальный:                         # server.py: копия основы с тестовой правкой адреса
        text = open(os.path.join(SRC, "server.py"), encoding="utf8", newline="").read()
        if ПАТЧ[0] not in text:
            sys.exit("В основе не нашёл строку с адресом сервера — правку для стенда нужно переделать.")
        text = text.replace(*ПАТЧ, 1)
        dst = os.path.join(dst_root, "server.py")
        old = open(dst, encoding="utf8", newline="").read() if os.path.exists(dst) else ""
        if old != text:
            print(("[сухо] " if сухо else "") + "server.py (с адресом 127.0.0.1)")
            n += 1
            if not сухо:
                open(dst, "w", encoding="utf8", newline="").write(text)
    if личное:
        for f in os.listdir(SRC):
            if f in ЛИЧНОЕ or any(re.fullmatch(m, f) for m in ЛИЧНОЕ_МАСКИ):
                dst = os.path.join(dst_root, f)
                if not os.path.exists(dst):
                    n += copy(os.path.join(SRC, f), dst, сухо)
    print("Изменено файлов:", n)


if __name__ == "__main__":
    main()
