# -*- coding: utf-8 -*-
"""Запуск Sow.exe в настоящей консоли и снятие содержимого её экрана.

Сервер — консольное приложение 2017 года; при перенаправлении stdout в файл
он печатает через консольный API, поэтому вывод виден только в реальной
консоли. Скрипт открывает окно консоли, подключается к ней и построчно
складывает всё новое в файл.

    python run_server.py [секунд_наблюдения]
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                ("wAttributes", ctypes.c_ushort), ("srWindow", SMALL_RECT),
                ("dwMaximumWindowSize", COORD)]


k32.CreateFileW.restype = wt.HANDLE
k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p,
                            wt.DWORD, wt.DWORD, wt.HANDLE]
k32.GetConsoleScreenBufferInfo.argtypes = [wt.HANDLE,
                                           ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
k32.ReadConsoleOutputCharacterW.argtypes = [wt.HANDLE, wt.LPWSTR, wt.DWORD,
                                            COORD, ctypes.POINTER(wt.DWORD)]


def open_conout():
    h = k32.CreateFileW("CONOUT$", GENERIC_READ | GENERIC_WRITE,
                        FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                        OPEN_EXISTING, 0, None)
    if h == wt.HANDLE(-1).value:
        return None
    return h


def snapshot(hout):
    """Видимые строки консоли + позиция курсора."""
    info = CONSOLE_SCREEN_BUFFER_INFO()
    if not k32.GetConsoleScreenBufferInfo(hout, ctypes.byref(info)):
        return None, None
    win = info.srWindow
    width = win.Right - win.Left + 1
    height = win.Bottom - win.Top + 1
    rows = []
    for i in range(height):
        buf = ctypes.create_unicode_buffer(width + 1)
        read = wt.DWORD(0)
        k32.ReadConsoleOutputCharacterW(hout, buf, width,
                                        COORD(win.Left, win.Top + i),
                                        ctypes.byref(read))
        rows.append(buf.value.rstrip())
    cur = (info.dwCursorPosition.Y, info.dwCursorPosition.X)
    return rows, cur


def main():
    watch = int(sys.argv[1]) if len(sys.argv) > 1 else 30  # 0 = держать вечно
    here = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(here, "server_console.log")

    exe = os.path.join(here, "Sow.exe")
    if not os.path.exists(exe):
        print("нет Sow.exe рядом со скриптом:", exe)
        return 2

    env = dict(os.environ)
    proc = subprocess.Popen([exe], cwd=here, env=env,
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
    print("запущен Sow.exe, PID", proc.pid)
    time.sleep(0.6)

    k32.FreeConsole()
    if not k32.AttachConsole(proc.pid):
        print("не удалось подключиться к консоли, код", ctypes.get_last_error())
        return 3

    hout = open_conout()
    if not hout:
        print("нет доступа к CONOUT$")
        return 4

    log = open(log_path, "w", encoding="utf-8")
    log.write("# консоль Sow.exe, PID %d\n" % proc.pid)
    prev = None
    start = time.time()
    while watch <= 0 or time.time() - start < watch:
        proc.poll()
        rows, cur = snapshot(hout)
        if rows is None:
            break
        if rows != prev:
            log.write("\n----- экран %s, курсор %s -----\n"
                      % (time.strftime("%H:%M:%S"), cur))
            for line in rows:
                if line.strip():
                    log.write(line + "\n")
            log.flush()
            prev = rows
        if proc.poll() is not None:
            log.write("\n# процесс завершился, код %s\n" % proc.returncode)
            break
        time.sleep(0.25)

    rows, cur = snapshot(hout)
    log.write("\n===== ИТОГОВЫЙ ЭКРАН =====\n")
    if rows:
        for line in rows:
            if line.strip():
                log.write(line + "\n")
    log.close()
    k32.FreeConsole()

    alive = proc.poll() is None
    print("жив:", alive, "код:", proc.returncode)
    print("лог:", log_path)
    return 0 if alive else 1


if __name__ == "__main__":
    sys.exit(main())
