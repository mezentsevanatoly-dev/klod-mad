"""Ручной режим: хоткеи из «жабы» пользователя через бота — команды идут в inbox.txt, бот пересылает их в игру.

pythonw tools\\manual_pad.py            (окно «Ручной режим»; включение — кнопка или ScrollLock)

Клавиши (NumLock включён) — как в конфиге JMC пользователя:
  NUM8 север  NUM5 юг  NUM4 запад  NUM6 восток  NUM7 вниз  NUM9 вверх  NUM1 смотреть  NUM2 к землетряс  NUM3 тр; мс; мв  NUM0 гр
  ADD  : гг !фраг; гг !пом; пом          MIN : очистить; вст; огл
  MUL  : гг !очистить; гг !вст; гг !од все   DIV : взя все все.труп; взя все
  F1 гг !к обря.очи  F2 гг !к сло.жи  F3 гг !к слов.свет  F5 гг !сумм  F6 гг !спать  F7 кар просн; зор просн  F8 гг !просн
  Shift+`  : очистить; вст; мол тут
(F9 #z, F10–F12 #con — команды самой «жабы», здесь не нужны.)
Оружие согруппника, выбитое масс. слабостью («X не смог удержать … и выронил»): окно само пишет `взять <слово>`, `дать <слово> <имя>`,
затем «экип» (`гг !очистить; гг !вст; гг !од все`), а в бою ещё и `гг !фраг` (вне боя фраг не нужен). Работает всегда, пока окно запущено.
Если шаг не вышел из-за закрытой/запертой двери («Попробуйте сначала открыть…», «…заперта/закрыта») — бот сам отпирает/открывает
(triggers.txt), а окно повторяет шаг (до двух раз).
Пока ручной режим включён, клавиши перехватываются везде (в том числе при наборе цифр с numpad в чате) — по умолчанию он
ВЫКЛЮЧЕН: включайте кнопкой или ScrollLock. Скрипт маршрута на это время лучше остановить. Ошибки — в manual_pad.log.
"""
import ctypes
import os
import re
import socket
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX, OUT = os.path.join(ROOT, "inbox.txt"), os.path.join(ROOT, "out.log")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_pad.log")
VK_SCROLL, VK_SHIFT, VK_OEM3 = 0x91, 0x10, 0xC0
MOVES = {0x68: "север", 0x65: "юг", 0x64: "запад", 0x66: "восток", 0x67: "вниз", 0x69: "вверх"}
KEYS = {                                   # виртуальный код -> (подпись, строки для игры)
    0x68: ("8 север", ["север"]), 0x65: ("5 юг", ["юг"]), 0x64: ("4 запад", ["запад"]), 0x66: ("6 восток", ["восток"]),
    0x67: ("7 вниз", ["вниз"]), 0x69: ("9 вверх", ["вверх"]),
    0x61: ("1 смотреть", ["смотреть"]), 0x62: ("2 к землетряс", ["к землетряс"]), 0x63: ("3 тр; мс; мв", ["тр", "мс", "мв"]),
    0x60: ("0 гр", ["гр"]),
    0x6B: ("+ фраг/пом", ["гг !фраг", "гг !пом", "пом"]), 0x6D: ("- очистить/вст/огл", ["очистить", "вст", "огл"]),
    0x6A: ("* группа: очистить/вст/од", ["гг !очистить", "гг !вст", "гг !од все"]),
    0x6F: ("/ взять с трупов", ["взя все все.труп", "взя все"]),
    0x70: ("F1", ["гг !к обря.очи"]), 0x71: ("F2", ["гг !к сло.жи"]), 0x72: ("F3", ["гг !к слов.свет"]),
    0x74: ("F5", ["гг !сумм"]), 0x75: ("F6", ["гг !спать"]), 0x76: ("F7", ["кар просн", "зор просн"]), 0x77: ("F8", ["гг !просн"]),
}
SHIFT_BACKTICK = ("Shift+` очистить/вст/мол тут", ["очистить", "вст", "мол тут"])
LOCKED = re.compile(r"Попробуйте сначала открыть|заперт[аоы]?\.|закрыт[аоы]?\.")
# масс. слабость выбила оружие у согруппника: «Элронг не смог удержать посох с символом башни и выронил его на землю.»
DROP = re.compile(r"^(?!Вы )(\S+) не смог(?:л[аи])? удержать (.+?) и выронил[аи]? \S+ на землю\.")
STATUS_LINE = re.compile(r"^\d+H \d+M \d+V .*Вых:")
NOT_LOCKED = re.compile(r"не заперт|не закрыт|уже ")


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def send(lines):
    with open(INBOX, "a", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")


def out_size():
    try:
        return os.path.getsize(OUT)
    except OSError:
        return 0


def new_text(since):
    try:
        with open(OUT, "rb") as f:
            f.seek(since)
            return f.read(20000).decode("utf-8", errors="replace")
    except OSError:
        return ""


MSDP = re.compile(r"^\[msdp\] комната (\d+) \| (.*?) \| (.*?) \| (\{.*\})\s*$")
SPEEDWALKS = os.path.join(ROOT, "speedwalks.txt")
PATHS = os.path.join(ROOT, "areas", "routes", "paths.tsv")


def rooms_since(offset):
    """Комнаты из out.log после offset (по строкам «[msdp] комната …»), подряд идущие повторы убраны."""
    out = []
    try:
        with open(OUT, "rb") as f:
            f.seek(offset)
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return out
    import ast
    for l in text.splitlines():
        m = MSDP.match(l)
        if m:
            try:
                ex = ast.literal_eval(m.group(4))
            except Exception:
                ex = {}
            if not out or out[-1][0] != m.group(1):
                out.append((m.group(1), m.group(2), m.group(3), {k: str(v) for k, v in ex.items()}))
    return out


def last_room():
    try:
        size = os.path.getsize(OUT)
        r = rooms_since(max(0, size - 60000))
        return r[-1] if r else None
    except OSError:
        return None


def shortest_walk(rooms):
    """Кратчайший путь от первой до последней записанной комнаты по рёбрам, которые мы видели (объезды и возвраты убираем).
    Возвращает строку спидволка «2ws3w» (n s e w u d) или None."""
    from collections import deque
    if len(rooms) < 2:
        return None
    seen = {r[0] for r in rooms}
    ex = {r[0]: r[3] for r in rooms}
    start, end = rooms[0][0], rooms[-1][0]
    prev, q = {start: None}, deque([start])
    while q:
        a = q.popleft()
        if a == end:
            break
        for d, b in ex.get(a, {}).items():
            if b in seen and b not in prev:
                prev[b] = (a, d.lower())
                q.append(b)
    if end not in prev:
        return None
    dirs, cur = [], end
    while prev[cur]:
        a, d = prev[cur]
        dirs.append(d)
        cur = a
    dirs.reverse()
    s, i = "", 0
    while i < len(dirs):
        j = i
        while j < len(dirs) and dirs[j] == dirs[i]:
            j += 1
        s += (str(j - i) if j - i > 1 else "") + dirs[i]
        i = j
    return s


def read_new(pos):
    """Новые байты out.log с позиции pos (до 60 КБ за раз): (текст, новая позиция)."""
    try:
        size = os.path.getsize(OUT)
        if size <= pos:
            return "", min(pos, size)
        with open(OUT, "rb") as f:
            f.seek(pos)
            raw = f.read(min(60000, size - pos))
        return raw.decode("utf-8", errors="replace"), pos + len(raw)
    except OSError:
        return "", pos


def main():
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", 47654))
    except OSError:
        return
    import tkinter as tk
    u = ctypes.windll.user32
    root = tk.Tk()
    root.title("Ручной режим")
    root.attributes("-topmost", True)
    root.geometry("+40+200")
    on = tk.BooleanVar(value=False)
    bg_off, bg_on = "#444", "#1f5a2a"
    root.configure(bg=bg_off)
    state = tk.Label(root, text="", fg="white", bg=bg_off, font=("Segoe UI", 12, "bold"))
    state.pack(padx=12, pady=(8, 2))
    last = tk.Label(root, text="", fg="#ffd9a0", bg=bg_off, font=("Segoe UI", 10))
    last.pack(padx=12)
    tk.Label(root, text="NUM: 8с 5ю 4з 6в 7вниз 9вверх  1смотр 2землетр 3тр/мс/мв 0гр  + фраг  - очистить/вст/огл  * группа  / труп\n"
                        "F1 F2 F3 F5 F6 F7 F8  Shift+` мол тут",
             fg="#ddd", bg=bg_off, font=("Segoe UI", 8), justify="left").pack(padx=12)

    def paint():
        bg = bg_on if on.get() else bg_off
        for wd in root.winfo_children():
            wd.configure(bg=bg)
        root.configure(bg=bg)
        state.config(text="РУЧНОЙ РЕЖИМ ВКЛЮЧЁН" if on.get() else "ручной режим выключен (ScrollLock или кнопка)")
        btn.config(text="Выключить" if on.get() else "Включить")

    def toggle():
        on.set(not on.get())
        paint()

    btn = tk.Button(root, text="Включить", command=toggle, font=("Segoe UI", 11), padx=10)
    btn.pack(pady=(4, 2))
    rec = {"offset": None, "from": None}

    def rec_toggle():
        from tkinter import simpledialog
        if rec["offset"] is None:                             # старт записи пути: запоминаем клетку и позицию в логе
            r = last_room()
            if not r:
                last.config(text="запись: не вижу текущую комнату в out.log")
                return
            rec.update(offset=os.path.getsize(OUT), **{"from": r})
            rec_btn.config(text="■ Стоп и записать путь")
            last.config(text=f"запись пути от {r[0]} {r[2]}")
            return
        rooms = rooms_since(rec["offset"])
        start = rec["from"]
        rooms = [start] + [r for r in rooms if r[0] != start[0] or rooms.index(r) > 0]
        rec.update(offset=None)
        rec_btn.config(text="● Старт записи пути")
        walk = shortest_walk(rooms)
        if not walk:
            last.config(text="запись: путь пустой или не связан (стоп без сохранения)")
            return
        end = rooms[-1]
        name = simpledialog.askstring("Имя спидволка", f"от {start[2]} до {end[2]}\nНазвание:", initialvalue=f"{start[2]} - {end[2]}", parent=root)
        if not name:
            last.config(text="запись отменена")
            return
        name = name.replace("=", "-").strip()
        with open(SPEEDWALKS, "a", encoding="utf-8") as f:
            f.write(f"# от {start[0]} {start[1]} | {start[2]} до {end[0]} {end[1]} | {end[2]} (записано {time.strftime('%d.%m %H:%M')})\n")
            f.write(f"{name} = {walk} @ {end[0]}\n")
            opp = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"}      # обратный путь сразу, в ту же запись
            back = "".join(f"{n}{opp[d]}" for n, d in reversed(re.findall(r"(\d*)([nsewud])", walk)))
            f.write(f"{name}_обр = {back} @ {start[0]}\n")
        os.makedirs(os.path.dirname(PATHS), exist_ok=True)
        with open(PATHS, "a", encoding="utf-8") as f:
            f.write("\t".join([time.strftime("%Y-%m-%dT%H:%M:%S"), name, start[0], start[2], end[0], end[2], walk]) + "\n")
        last.config(text=f"записано: {name} = {walk}")

    rec_btn = tk.Button(root, text="● Старт записи пути", command=rec_toggle, font=("Segoe UI", 10), padx=10)
    rec_btn.pack(pady=(0, 8))
    paint()
    watched = list(KEYS) + [VK_SCROLL, VK_OEM3]
    prev = {vk: False for vk in watched}
    pend = {"cmd": None, "t": 0.0, "size": 0, "tries": 0, "retry_at": None}
    logpos, drops, battle = [out_size()], {"items": [], "t": 0.0}, {"on": False}

    def go(label, lines, move=None):
        send(lines)
        last.config(text="→ " + label)
        if move:
            pend.update(cmd=move, t=time.time(), size=out_size(), tries=0, retry_at=None)
        else:
            pend["cmd"] = None

    def poll():
        try:
            for vk in watched:
                down = bool(u.GetAsyncKeyState(vk) & 0x8000)
                if down and not prev[vk]:                     # фронт нажатия
                    if vk == VK_SCROLL:
                        toggle()
                    elif on.get():
                        if vk == VK_OEM3:
                            if u.GetAsyncKeyState(VK_SHIFT) & 0x8000:
                                go(*SHIFT_BACKTICK)
                        else:
                            label, lines = KEYS[vk]
                            go(label, lines, MOVES.get(vk))
                prev[vk] = down
            # оружие согруппника, выбитое масс. слабостью: поднять, отдать, экипировать; «гг !фраг» — только если идёт бой
            raw_new, logpos[0] = read_new(logpos[0])
            for ln in raw_new.splitlines():
                m = DROP.match(ln)
                if m:
                    kw = m.group(2).replace("*", "").split()[0][:5].lower()      # «посох с символом башни» -> «посох», «голову…» -> «голов»
                    drops["items"].append((m.group(1).lower(), kw))
                    drops["t"] = time.time()
                elif STATUS_LINE.match(ln):
                    battle["on"] = "] [" in ln or "[Тадия:" in ln                 # в бою в строке статуса есть [Я:…] [моб:…]
            if drops["items"] and time.time() - drops["t"] > 1.2:                  # подождали, пока придут все сообщения о выпавшем
                lines = []
                for who, kw in dict.fromkeys(drops["items"]):
                    lines += [f"взять {kw}", f"дать {kw} {who}"]
                lines += ["гг !очистить", "гг !вст", "гг !од все"]                 # макрос «экип» — экипироваться после очистки
                if battle["on"]:
                    lines.append("гг !фраг")                                       # в бою — сразу в драку; вне боя не нужно
                send(lines)
                last.config(text="оружие вернула: " + ", ".join(f"{k}→{w}" for w, k in dict.fromkeys(drops["items"])) + (" + фраг" if battle["on"] else ""))
                drops["items"] = []
            # шаг упёрся в закрытую/запертую дверь: бот открывает по триггеру, мы повторяем шаг
            if pend["cmd"] and on.get():
                now = time.time()
                if pend["retry_at"] is None and now - pend["t"] < 2.5:
                    txt = new_text(pend["size"])
                    if any(LOCKED.search(l) and not NOT_LOCKED.search(l) for l in txt.splitlines()):
                        pend["retry_at"] = now + 1.8
                elif pend["retry_at"] and now >= pend["retry_at"]:
                    pend["tries"] += 1
                    send([pend["cmd"]])
                    last.config(text=f"→ {pend['cmd']} (после двери, повтор {pend['tries']})")
                    if pend["tries"] >= 2:
                        pend["cmd"] = None
                    else:
                        pend.update(t=now, size=out_size(), retry_at=None)
                elif now - pend["t"] >= 2.5 and pend["retry_at"] is None:
                    pend["cmd"] = None
        except Exception:
            log(traceback.format_exc())
        root.after(25, poll)

    log("запущено")
    poll()
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
