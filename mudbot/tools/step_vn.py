"""Шаги Айлины с номером клетки (vnum) после каждого шага.
Запуск: python -X utf8 tools/step_vn.py "з" "ю" "убить жук" ...
Для каждой команды: отправить в жабу Айлины, подождать, записать '## <vnum>' в claude_game.log и вывести ответ игры + vnum.
Если висит окно 'Error in JMC scripts.', его закрывает (иначе жаба не принимает ввод)."""
import os, sys, time, ctypes, re
from ctypes import wintypes
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(__file__))
import jmc

u = ctypes.windll.user32
WNDENUM = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def close_errors():
    n = 0
    for _ in range(10):
        found = []

        def cb(h, _):
            t = ctypes.create_unicode_buffer(256)
            u.GetWindowTextW(h, t, 256)
            if t.value == "Error in JMC scripts." and u.IsWindowVisible(h):
                found.append(h)
            return True
        u.EnumWindows(WNDENUM(cb), 0)
        if not found:
            break
        for h in found:
            u.PostMessageW(h, 0x0010, 0, 0)
            n += 1
        time.sleep(0.5)
    return n


def main(cmds, wait=2.0):
    close_errors()
    edit = jmc.find_input(jmc.find_window())
    for c in cmds:
        start = jmc.log_size()
        jmc.type_line(c, True, edit)
        time.sleep(wait)
        jmc.type_line("#scr ClaudeLog.note($MsdpRoomVnum)", True, edit)
        time.sleep(0.8)
        lines = [re.sub(r"^\d\d:\d\d:\d\d ", "", l) for l in jmc.read_log(start)]
        lines = [l for l in lines if l.strip() and "Союзники" not in l and not l.startswith(">> #scr ClaudeLog")]
        vn = next((l[3:] for l in reversed(lines) if re.fullmatch(r"## \d+", l)), "?")
        print(f"=== {c}  [vnum {vn}]")
        print("\n".join(l for l in lines if not l.startswith("## ") and not re.match(r"^\d+H ", l)))
    close_errors()


if __name__ == "__main__":
    main(sys.argv[1:])
