"""Окошко с кнопками поверх всех окон, пока бот подозревает проверку присутствия (есть файл alarm.flag).

pythonw tools\\alarm_popup.py            — слушать alarm.flag (бот сам запускает окно при тревоге);
pythonw tools\\alarm_popup.py --demo     — показать окно на 90 секунд, чтобы проверить кнопки.
Кнопки (нажимает человек):
  1. «Мол тут»       — строка «мол тут» в inbox.txt: бот пересылает её в игру (ответ на проверку даёт человек);
  2. «Консоль»       — своё окно: живой хвост out.log (что идёт в игре) и строка ввода -> inbox.txt -> игра;
  3. «/known»        — запомнить подозрительные строки как обычные и продолжить (ctl.txt);
  4. «/ok»           — продолжить без запоминания (ctl.txt).
Бот читает из ctl.txt только /ok и /known. Одновременно живёт один экземпляр окна; ошибки пишутся в alarm_popup.log.
"""
import ctypes
import os
import socket
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAG, CTL, INBOX, LINK = (os.path.join(ROOT, n) for n in ("alarm.flag", "ctl.txt", "inbox.txt", "link.flag"))
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarm_popup.log")
PRAY = "мол тут"
DEMO = "--demo" in sys.argv
HOLD = "--hold" in sys.argv          # окно висит, пока процесс не закроют (по просьбе пользователя)


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def append(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def focus_console():
    u = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, _):
        n = u.GetWindowTextLengthW(h)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, buf, n + 1)
            if "claude" in buf.value.lower() and u.IsWindowVisible(h):
                found.append(h)
        return True

    u.EnumWindows(cb, 0)
    if not found:
        log("окно Claude не найдено")
        return False
    h = found[0]
    u.ShowWindow(h, 9)                                   # SW_RESTORE (из свёрнутого)
    u.keybd_event(0x12, 0, 0, 0)                         # «Alt»: Windows разрешает перехват переднего плана
    u.SetForegroundWindow(h)
    u.keybd_event(0x12, 0, 2, 0)
    return True


OUT = os.path.join(ROOT, "out.log")
_console = {}


def open_console(root, tk):
    """Своё окно «консоль»: живой хвост out.log (то, что идёт в игре) и строка ввода -> inbox.txt -> игра.
    Вкладками Claude оно не управляет: кнопка раньше открывала не ту вкладку."""
    win = _console.get("win")
    if win is not None and win.winfo_exists():
        win.deiconify()
        win.lift()
        return True
    win = tk.Toplevel(root)
    _console["win"] = win
    win.title("Консоль бота (out.log)")
    win.attributes("-topmost", True)
    win.geometry("900x520+60+120")
    box = tk.Text(win, bg="#111", fg="#ddd", font=("Consolas", 10), wrap="word")
    box.pack(fill="both", expand=True)
    entry = tk.Entry(win, font=("Consolas", 11))
    entry.pack(fill="x")
    entry.focus_set()

    def send(_e=None):
        line = entry.get().strip()
        if line:
            append(INBOX, line)                          # бот пересылает строку из inbox.txt в игру
            entry.delete(0, "end")

    entry.bind("<Return>", send)
    state = {"size": -1}

    def refresh():
        if not win.winfo_exists():
            return
        try:
            size = os.path.getsize(OUT)
            if size != state["size"]:
                state["size"] = size
                with open(OUT, "rb") as f:
                    f.seek(max(0, size - 12000))
                    data = f.read().decode("utf-8", errors="replace")
                lines = [l for l in data.splitlines()[1:] if l.strip()]
                box.delete("1.0", "end")
                box.insert("end", "\n".join(lines[-80:]))
                box.see("end")
        except OSError:
            pass
        win.after(700, refresh)

    refresh()
    return True


def main():
    lock = socket.socket()                               # один экземпляр: второй запуск тихо выходит
    try:
        lock.bind(("127.0.0.1", 47653))
    except OSError:
        return
    import tkinter as tk
    bg = "#7a1f1f"
    root = tk.Tk()
    root.title("Проверка присутствия?")
    root.attributes("-topmost", True)
    root.configure(bg=bg)
    txt = tk.Label(root, text="", fg="white", bg=bg, font=("Segoe UI", 11, "bold"), wraplength=520, justify="left")
    txt.pack(padx=12, pady=(10, 4))
    status = tk.Label(root, text="", fg="#ffd9a0", bg=bg, font=("Segoe UI", 10))
    status.pack(padx=12)
    row = tk.Frame(root, bg=bg)
    row.pack(padx=12, pady=(4, 10))

    def act(label, fn):
        def run():
            try:
                ok = fn()
                status.config(text=f"{label}: {'готово' if ok is not False else 'не получилось (см. alarm_popup.log)'}")
            except Exception:
                log(traceback.format_exc())
                status.config(text=f"{label}: ошибка (см. alarm_popup.log)")
        return run

    buttons = (("Мол тут", lambda: append(INBOX, PRAY)), ("Консоль", lambda: open_console(root, tk)),
               ("/known", lambda: append(CTL, "/known")), ("/ok", lambda: append(CTL, "/ok")))
    btn = {}
    for label, fn in buttons:
        btn[label] = tk.Button(row, text=label, command=act(label, fn), font=("Segoe UI", 11), padx=12, pady=6)
        btn[label].pack(side="left", padx=4)
    root.withdraw()
    t0 = time.time()

    def poll():
        try:
            link = os.path.exists(LINK)
            alarm = os.path.exists(FLAG) or link or HOLD or (DEMO and time.time() - t0 < 90)
            if alarm:
                try:
                    src = FLAG if os.path.exists(FLAG) else LINK
                    lines = open(src, encoding="utf-8").read() if os.path.exists(src) else "ТЕСТ окна"
                except OSError:
                    lines = ""
                head, _, rest = lines.partition("\n")
                if head.startswith("СВЯЗЬ ПРОПАЛА"):
                    title, rest = "СВЯЗЬ С ИГРОЙ ПРОПАЛА!", lines
                    btn["Мол тут"].config(state="disabled")
                elif head.startswith("ТИП: ручная"):
                    title = "РУЧНАЯ ПРОВЕРКА (вопрос)! Ответьте в игре сами, автоответа нет."
                    btn["Мол тут"].config(state="disabled")
                elif head.startswith("ТИП: авто"):
                    title = "АВТОПРОВЕРКА (бессмысленные строки): её проходят все в группе, «Мол тут»."
                    btn["Мол тут"].config(state="normal")
                else:
                    title, rest = "Похоже на проверку присутствия!", lines
                    btn["Мол тут"].config(state="normal")
                txt.config(text=title + "\n" + rest[:300])
                if root.state() == "withdrawn":
                    root.deiconify()
                    root.geometry("+40+40")
                root.attributes("-topmost", True)
                root.lift()
            elif root.state() != "withdrawn":
                root.withdraw()
                status.config(text="")
            if DEMO and time.time() - t0 > 93:
                root.destroy()
                return
        except Exception:
            log(traceback.format_exc())
        root.after(500, poll)

    log("запущено" + (" (демо)" if DEMO else ""))
    poll()
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
