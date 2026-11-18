"""Управление окном JMC (Клод мад\\JMC\\jmc.exe) из командной строки: набрать команду в строку ввода, снимок окна.
python tools/jmc.py type "#alias {x} {y} {claude}" [--force]   -> набрать в JMC и нажать Enter
python tools/jmc.py cmds файл.txt [пауза_сек]                   -> набрать построчно (пустые и «##» пропускаются)
python tools/jmc.py set "#action {^Вы ослепли} {колд сл.свет} {5} {claude}"
                                                                -> дописать строку в JMC\\claude.set и набрать её в JMC
python tools/jmc.py reload                                      -> #read claude.set (перечитать мои алиасы/триггеры)
python tools/jmc.py log start|stop                              -> писать вывод игры в mudbot/jmc_out.log (включать ПОСЛЕ входа в игру)
python tools/jmc.py do "команда" [сек]                          -> набрать в JMC и показать, что ответила игра (по логу)
python tools/jmc.py tail [N]                                    -> последние N строк jmc_out.log
python tools/jmc.py read                                        -> что сейчас в строке ввода
python tools/jmc.py shot [файл.png]                             -> снимок окна JMC (по умолчанию mudbot/jmc_shot.png)
Правила: только когда пользователь попросил. Если в строке ввода уже есть текст (пользователь печатает), type отказывается
(код 2): без --force строку не трогаем. Логин и пароль не набираем никогда. Мои алиасы/триггеры всегда в группе «claude»
(#group disable claude — выключить все). Текст команд — Unicode, JMC принимает его как cp1251.
"""
import ctypes
import os
import sys
import time
from ctypes import wintypes

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
try:
    u32.SetProcessDPIAware()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # ...\mudbot
JMC_DIR = os.path.join(os.path.dirname(ROOT), "JMC")           # ...\Клод мад\JMC
CLAUDE_SET = os.path.join(JMC_DIR, "claude.set")

WM_SETTEXT, WM_GETTEXT, WM_GETTEXTLENGTH = 0x000C, 0x000D, 0x000E
WM_KEYDOWN, WM_KEYUP, WM_CHAR, VK_RETURN = 0x0100, 0x0101, 0x0102, 0x0D

u32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
u32.SendMessageW.restype = wintypes.LPARAM
u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
WNDENUM = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _exe_path(pid):
    h = k32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(1024)
        k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        return buf.value
    finally:
        k32.CloseHandle(h)


def find_window():
    """Главное окно jmc.exe из папки Клод мад\\JMC (иначе любое окно JMC)."""
    found = []

    def cb(h, _):
        if u32.IsWindowVisible(h):
            title = ctypes.create_unicode_buffer(256)
            u32.GetWindowTextW(h, title, 256)
            if title.value.startswith("Jaba MUD Client"):
                pid = wintypes.DWORD()
                u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                found.append((h, _exe_path(pid.value)))
        return True

    u32.EnumWindows(WNDENUM(cb), 0)
    tgt = os.environ.get("JMC_TARGET") or JMC_DIR      # JMC_TARGET = папка нужной жабы (Инка/Айлина)
    mine = [h for h, p in found if os.path.normcase(p).startswith(os.path.normcase(tgt))]
    if mine:
        return mine[0]
    if found:
        return found[0][0]
    sys.exit("окно JMC не найдено (запустите JMC\\jmc.exe)")


def find_input(main):
    res = []

    def cb(h, _):
        cls = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(h, cls, 64)
        if cls.value == "Edit" and u32.GetDlgCtrlID(h) == 1000:
            res.append(h)
            return False
        return True

    u32.EnumChildWindows(main, WNDENUM(cb), 0)
    if not res:
        sys.exit("строка ввода JMC не найдена")
    return res[0]


def get_text(edit):
    n = u32.SendMessageW(edit, WM_GETTEXTLENGTH, 0, 0)
    buf = ctypes.create_unicode_buffer(n + 2)
    u32.SendMessageW(edit, WM_GETTEXT, n + 1, ctypes.addressof(buf))
    return buf.value


def type_line(text, force=False, edit=None):
    edit = edit or find_input(find_window())
    cur = get_text(edit)
    if cur.strip() and not force:
        sys.exit(f"в строке ввода уже есть текст ({cur!r}) — пользователь печатает; не трогаю (--force: перезаписать)")
    buf = ctypes.create_unicode_buffer(text)         # буфер должен жить до конца вызова
    u32.SendMessageW(edit, WM_SETTEXT, 0, ctypes.addressof(buf))
    time.sleep(0.15)
    u32.PostMessageW(edit, WM_KEYDOWN, VK_RETURN, 0x001C0001)
    u32.PostMessageW(edit, WM_CHAR, VK_RETURN, 0x001C0001)
    u32.PostMessageW(edit, WM_KEYUP, VK_RETURN, 0xC01C0001)
    time.sleep(0.25)


def shot(path=None):
    """Снимок окна JMC через PrintWindow: работает, даже если сверху другие окна."""
    from PIL import Image
    gdi = ctypes.windll.gdi32
    main = find_window()
    r = wintypes.RECT()
    u32.GetWindowRect(main, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = u32.GetWindowDC(main)
    mdc = gdi.CreateCompatibleDC(hdc)
    bmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(mdc, bmp)
    u32.PrintWindow(main, mdc, 2)                  # PW_RENDERFULLCONTENT

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("x", wintypes.LONG), ("y", wintypes.LONG),
                    ("c", wintypes.DWORD), ("i", wintypes.DWORD)]

    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi.DeleteObject(bmp)
    gdi.DeleteDC(mdc)
    u32.ReleaseDC(main, hdc)
    path = path or os.path.join(ROOT, "jmc_shot.png")
    Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1).save(path)
    return path


def _jmc_dir():
    """Папка запущенного jmc.exe (их несколько: Клод мад\\JMC, Desktop\\Тадия…): лог кладём рядом с ним, без пробелов в пути."""
    if os.environ.get("JMC_TARGET"):
        return os.environ["JMC_TARGET"]
    try:
        import subprocess
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-Process jmc -ErrorAction SilentlyContinue | Select-Object -First 1).Path"],
                             capture_output=True, text=True, encoding="utf-8", timeout=15).stdout.strip()
        return os.path.dirname(out) if out else None
    except Exception:
        return None


_JD = _jmc_dir()
USE_MODULE = bool(_JD and os.path.basename(_JD).lower() not in ("jmc",) and os.path.exists(os.path.join(_JD, "scripts", "ClaudeLog.js")))
if USE_MODULE:                                    # JMC с моим модулем scripts/ClaudeLog.js: он сам пишет строки в claude_game.log (встроенный #log там пишет 0 байт)
    LOG = os.path.join(_JD, "claude_game.log")
    LOG_REL = "claude_game.log"
elif _JD and os.path.basename(_JD).lower() not in ("jmc",):        # запущен не штатный JMC из «Клод мад\\JMC»: пишем лог в его папку
    LOG = os.path.join(_JD, "claude_out.log")
    LOG_REL = "claude_out.log"
else:
    LOG = os.path.join(ROOT, "jmc_out.log")      # сюда JMC пишет вывод игры (#log), cp1251
    LOG_REL = "../mudbot/jmc_out.log"            # тот же файл относительно папки JMC; только «/»: JMC съедает «\»


def log_start(force=False):
    """Включить запись вывода игры. ТОЛЬКО после входа в игру: в лог попадает и то, что набрано в строке ввода."""
    type_line(f"#log {LOG_REL} append", force)


def log_stop(force=False):
    type_line("#log", force)


def log_size():
    return os.path.getsize(LOG) if os.path.exists(LOG) else 0


def read_log(start=0):
    import re
    if not os.path.exists(LOG):
        return []
    with open(LOG, "rb") as f:
        f.seek(start)
        text = f.read().decode("cp1251", errors="replace")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text).replace("\r", "")
    return text.split("\n")


def flush_log(force=False):
    """JMC держит лог в буфере и пишет его на диск при закрытии: закрыть и открыть заново (append)."""
    type_line(f"#log;#log {LOG_REL} append", force)
    time.sleep(0.5)


POS_FILE = os.path.join(ROOT, ".jmc_pos")        # сколько строк лога уже выдано (между запусками)
SKIP = ("#Logging", "Log: ", "Logging started")


def _get_pos(lines):
    try:
        p = int(open(POS_FILE).read().strip())
    except (OSError, ValueError):
        p = 0
    return p if p <= len(lines) else 0


def do_many(cmds, wait=1.5, force=False):
    """Набрать команды по очереди (пауза wait после каждой), потом ОДИН раз сбросить лог на диск (одна служебная
    строка «#Logging…» в окне JMC на весь пакет) и вернуть ответы игры по каждой команде: [(команда, [строки])].
    Границы ответов — по эхо набранной команды в логе (JMC пишет её в лог)."""
    edit = find_input(find_window())
    if USE_MODULE:                                           # модуль ClaudeLog пишет сам: #log в окне не трогаем, ответ — всё новое после команд
        import re
        start = log_size()
        for c in cmds:
            type_line(c, force, edit)
            time.sleep(wait)
        time.sleep(1.0)
        lines = [re.sub(r"^\d\d:\d\d:\d\d ", "", l) for l in read_log(start)]
        return [(" | ".join(cmds), [l for l in lines if l.strip()])]
    type_line(f"#log;#log {LOG_REL} append", force, edit)   # лог мог быть закрыт пользователем: открыть наш файл заранее
    time.sleep(0.5)
    start = log_size()                                       # всё, что было до этого, уже на диске
    for c in cmds:
        type_line(c, force, edit)
        time.sleep(wait)
    type_line(f"#log;#log {LOG_REL} append", force, edit)   # закрыть (сбросить буфер) и открыть заново — одной строкой
    time.sleep(0.5)
    lines = read_log(start)
    new = lines
    pos = 0
    out, i = [], 0
    for c in cmds:
        key = c.strip()
        j = next((k for k in range(i, len(new)) if key and new[k].strip() == key), None)
        if j is None:
            out.append((c, []))
            continue
        out.append((c, j))
        i = j + 1
    res = []
    for n, (c, j) in enumerate(out):
        if isinstance(j, list):
            res.append((c, j))
            continue
        end = next((m for (_, jj) in out[n + 1:] if isinstance(jj, int) for m in [jj]), len(new))
        res.append((c, [l for l in new[j + 1:end] if l.strip() and not l.startswith(SKIP)]))
    if len(cmds) == 1 and all(not r for _, r in res):          # пустая команда (Enter): всё новое
        res = [(cmds[0], [l for l in new if l.strip() and not l.startswith(SKIP)])]
    return res


def do(cmd, wait=1.5, force=False):
    """Одна команда: набрать, подождать wait, вернуть строки ответа игры."""
    return do_many([cmd], wait, force)[0][1]


def add_to_claude_set(line):
    os.makedirs(JMC_DIR, exist_ok=True)
    old = ""
    if os.path.exists(CLAUDE_SET):
        old = open(CLAUDE_SET, encoding="cp1251").read()
    if line not in old.splitlines():
        with open(CLAUDE_SET, "a", encoding="cp1251", newline="") as f:
            if old and not old.endswith("\n"):
                f.write("\r\n")
            f.write(line + "\r\n")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd, args = argv[1], argv[2:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    if cmd == "type" and args:
        type_line(" ".join(args), force)
        print("набрано:", " ".join(args))
    elif cmd == "cmds" and args:
        pause = float(args[1]) if len(args) > 1 else 0.6
        edit = find_input(find_window())
        for line in open(args[0], encoding="utf-8"):
            line = line.rstrip("\r\n")
            if line.strip() and not line.startswith("##"):
                type_line(line, force, edit)
                time.sleep(pause)
        print("готово")
    elif cmd == "set" and args:
        line = " ".join(args)
        add_to_claude_set(line)
        type_line(line, force)
        print("записано в claude.set и набрано:", line)
    elif cmd == "log" and args and args[0] in ("start", "stop"):
        (log_start if args[0] == "start" else log_stop)(force)
        print("лог:", args[0], LOG)
    elif cmd == "tail":
        n = int(args[0]) if args else 40
        flush_log(force)
        print("\n".join(read_log(0)[-n:]))
    elif cmd == "do" and args:
        wait = 1.5
        if len(args) > 1:
            try:
                wait = float(args[-1])
                args = args[:-1]
            except ValueError:
                pass
        print("\n".join(do(" ".join(args), wait, force)))
    elif cmd == "reload":
        type_line("#read claude.set", force)
        print("набрано: #read claude.set")
    elif cmd == "read":
        print(repr(get_text(find_input(find_window()))))
    elif cmd == "shot":
        print(shot(args[0] if args else None))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
