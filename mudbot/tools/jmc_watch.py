"""Наблюдатель за ботом в JMC. Читает Тадия\\claude_game.log, ничего в игру не шлёт.

  pythonw tools/jmc_watch.py            -> окно для пользователя (всегда сверху) + запись событий для Claude
  python  tools/jmc_watch.py wait [сек] -> ждёт новое событие (СТОЯНИЕ, СТОП, КОНЕЦ ЗОНЫ, СМЕРТЬ...) и печатает его (для Claude: запускать в фоне)
  python  tools/jmc_watch.py status     -> краткое состояние
  python  tools/jmc_watch.py say "текст"  -> строка в окно пользователя (что делает Claude)
  python  tools/jmc_watch.py call "текст" -> окно синее + сигнал: «позови пользователя» (зона пройдена и т.п.)
Данные: mudbot/data/jmc_watch/{status.json,events.jsonl,cursor.txt,call.flag}
События: BOT_START, BOT_STOP, ZONE_END, STALL (бот >STALL_SEC без шага/убийства), NOLOG (тишина в логе), DEATH, FAIL (ход не прошёл), BATTLE_BLOCK.
"""
import json, os, re, socket, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "jmc_watch")
LOG = os.environ.get("JMC_WATCH_LOG", r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log")
if os.environ.get("JMC_WATCH_DATA"):
    DATA = os.environ["JMC_WATCH_DATA"]
STATUS = os.path.join(DATA, "status.json")
EVENTS = os.path.join(DATA, "events.jsonl")
CURSOR = os.path.join(DATA, "cursor.txt")
CALL = os.path.join(DATA, "call.flag")
STALL_SEC = 60
NOLOG_SEC = 10          # окно жёлтое
NOLOG_EVENT_SEC = 60    # событие для Claude
LOCK_PORT = 47811
os.makedirs(DATA, exist_ok=True)

LINE = re.compile(r"^(\d\d:\d\d:\d\d) (.*)$")
STEP = re.compile(r"^## STEP (\d+) vn=(\S*) cmd=(.*)$")
KILL = re.compile(r"^(.+?) мертв[аоы]?\. R\.I\.P\.")
PROMPT = re.compile(r"^(\d+)H (\d+)M (\d+)V (\d+)X")
DEATH = re.compile(r"^Вы (мертвы|умерли|погибли)|^Вы мертвы")
FAIL = re.compile(r"не можете идти|Попробуйте сначала открыть|Дверь заперта|Вы не владеете")


def now():
    return time.strftime("%H:%M:%S")


QUIET = False


def add_event(typ, text, ctx=None):
    if QUIET:
        return None
    n = 1
    if os.path.exists(EVENTS):
        with open(EVENTS, "rb") as f:
            n = sum(1 for _ in f) + 1
    ev = {"id": n, "t": now(), "type": typ, "text": text, "ctx": ctx or []}
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def read_events(after=0):
    out = []
    if os.path.exists(EVENTS):
        for ln in open(EVENTS, encoding="utf-8"):
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if e["id"] > after:
                out.append(e)
    return out


class Watch:
    def __init__(self):
        self.pos = 0
        self.tail = []
        self.bot_on = False
        self.zone = ""
        self.total = 0
        self.step = None            # (idx, vn, cmd)
        self.kills = 0
        self.hp = ""
        self.last_progress = time.time()
        self.last_line = time.time()
        self.paused_until = 0
        self.stall_flag = False
        self.nolog_flag = False
        self.nolog_event = False
        self.start_time = None
        self.first_vn = None
        # восстановить состояние бота по хвосту лога (без событий)
        global QUIET
        if os.path.exists(LOG):
            self.pos = max(0, os.path.getsize(LOG) - 400000)
            QUIET = True
            try:
                self.feed(skip_first=True)
            finally:
                QUIET = False
            self.last_progress = self.last_line = time.time()

    def feed(self, skip_first=False):
        if not os.path.exists(LOG):
            return
        size = os.path.getsize(LOG)
        if size < self.pos:
            self.pos = 0
        if size == self.pos:
            return
        with open(LOG, "rb") as f:
            f.seek(self.pos)
            data = f.read()
        # не берём недописанную последнюю строку
        cut = data.rfind(b"\n")
        if cut < 0:
            return
        self.pos += cut + 1
        rows = data[:cut].decode("cp1251", errors="replace").replace("\r", "").split("\n")
        if skip_first:
            rows = rows[1:]
        for raw in rows:
            self.line(raw)

    def ctx(self, n=14):
        return self.tail[-n:]

    def line(self, raw):
        m = LINE.match(raw)
        if not m:
            return
        body = m.group(2)
        self.last_line = time.time()
        self.nolog_flag = False
        self.nolog_event = False
        self.tail.append(raw[:160])
        del self.tail[:-40]
        if body.startswith("## "):
            s = STEP.match(body)
            if s:
                self.step = (int(s.group(1)), s.group(2), s.group(3))
                self.bot_on = True
                if self.first_vn is None:
                    self.first_vn = s.group(2)
                self.last_progress = time.time()
                self.stall_flag = False
            elif body.startswith("## BOT_START"):
                self.bot_on = True
                self.kills = 0
                self.step = None
                self.first_vn = None
                self.start_time = time.time()
                self.last_progress = time.time()
                self.stall_flag = False
                mm = re.search(r"zone=(\S*) steps=(\d+)", body)
                if mm:
                    self.zone, self.total = mm.group(1), int(mm.group(2))
                add_event("BOT_START", body[3:], self.ctx(4))
            elif body.startswith("## BOT_STOP"):
                self.bot_on = False
                add_event("BOT_STOP", body[3:], self.ctx())
            elif body.startswith("## ZONE_END"):
                self.bot_on = False
                add_event("ZONE_END", "%s; убийств %d; последняя клетка %s" % (body[3:], self.kills, self.step[1] if self.step else "?"), self.ctx())
            elif body.startswith("## AREA"):
                self.last_progress = time.time()
                self.stall_flag = False
                mm = re.search(r"AREA_WAIT secs=(\d+)", body)
                if mm:
                    self.paused_until = time.time() + int(mm.group(1)) + 20
                add_event("AREA", body[3:], self.ctx(4))
            elif body.startswith("## MOVE_BLOCKED_BATTLE"):
                add_event("BATTLE_BLOCK", body[3:], self.ctx(6))
            return
        if "Вы присели и дали отдохнуть" in body:      # бот отдыхает (мало мувов): паузу не считаем застоем
            self.paused_until = max(self.paused_until, time.time() + 40)
            self.last_progress = time.time()
        k = KILL.match(body)
        if k:
            self.kills += 1
            self.last_progress = time.time()
            self.stall_flag = False
        p = PROMPT.match(body)
        if p:
            self.hp = "%sH %sM %sV %sX" % p.groups()
        if self.bot_on and DEATH.search(body):
            add_event("DEATH", body, self.ctx())
        if self.bot_on and FAIL.search(body):
            add_event("FAIL", body, self.ctx(8))

    def tick(self):
        t = time.time()
        paused = t < self.paused_until
        if self.bot_on and not paused and not self.stall_flag and t - self.last_progress > STALL_SEC:
            self.stall_flag = True
            add_event("STALL", "нет шага/убийства %d с; шаг %s" % (t - self.last_progress, self.step), self.ctx(20))
        if self.bot_on and not paused and not self.nolog_flag and t - self.last_line > NOLOG_SEC:
            self.nolog_flag = True
        if self.bot_on and not paused and not self.nolog_event and t - self.last_line > NOLOG_EVENT_SEC:
            self.nolog_event = True
            add_event("NOLOG", "в логе тишина %d с (связь/JMC/бот встал?)" % (t - self.last_line), self.ctx(10))

    def status(self):
        t = time.time()
        st = {"time": now(), "bot_on": self.bot_on, "zone": self.zone, "total": self.total,
              "step": self.step[0] if self.step else None, "vn": self.step[1] if self.step else None,
              "cmd": self.step[2] if self.step else None, "kills": self.kills, "hp": self.hp,
              "idle_progress": int(t - self.last_progress), "idle_log": int(t - self.last_line),
              "stall": self.stall_flag, "nolog": self.nolog_flag}
        with open(STATUS, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)
        return st


def cmd_wait(timeout):
    cur = int(open(CURSOR).read().strip()) if os.path.exists(CURSOR) else 0
    end = time.time() + timeout
    while time.time() < end:
        evs = [e for e in read_events(cur) if e["type"] not in ("SAY", "BOT_START", "BATTLE_BLOCK", "AREA")]
        allevs = read_events(cur)
        if evs:
            open(CURSOR, "w").write(str(allevs[-1]["id"]))
            for e in evs:
                print("[%s] %s: %s" % (e["t"], e["type"], e["text"]))
                for c in e["ctx"][-14:]:
                    print("    " + c)
            return 0
        if allevs:
            cur = allevs[-1]["id"]
            open(CURSOR, "w").write(str(cur))
        time.sleep(2)
    print("TIMEOUT: событий нет %d с" % timeout)
    return 0


def gui():
    try:
        lock = socket.socket()
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        return 0                                   # уже запущен
    import tkinter as tk
    try:
        import winsound
    except ImportError:
        winsound = None
    w = Watch()
    root = tk.Tk()
    root.title("Бот JMC")
    root.attributes("-topmost", True)
    root.geometry("430x210+20+20")
    root.configure(bg="#1d3a1d")
    head = tk.Label(root, text="", font=("Consolas", 11, "bold"), fg="white", bg="#1d3a1d", anchor="w", justify="left")
    head.pack(fill="x", padx=6, pady=(4, 0))
    body = tk.Label(root, text="", font=("Consolas", 9), fg="#dddddd", bg="#1d3a1d", anchor="nw", justify="left", wraplength=415)
    body.pack(fill="both", expand=True, padx=6)
    btn = tk.Button(root, text="Принял", command=lambda: os.path.exists(CALL) and os.remove(CALL))
    btn.pack(side="bottom", pady=3)
    shown = {"last": 0, "beep": 0}

    def recolor(c):
        for x in (root, head, body):
            x.configure(bg=c)

    def loop():
        try:
            w.feed()
            w.tick()
            st = w.status()
            evs = read_events(max(0, (read_events()[-1]["id"] if read_events() else 0) - 6))
            lines = ["[%s] %s %s" % (e["t"], e["type"], e["text"][:70]) for e in evs]
            called = os.path.exists(CALL)
            if called:
                recolor("#1d3a7a")
                txt = open(CALL, encoding="utf-8").read().strip()
                head.config(text="ПОЗОВИ ПОЛЬЗОВАТЕЛЯ: " + txt[:60])
                if winsound and time.time() - shown["beep"] > 20:
                    shown["beep"] = time.time()
                    winsound.MessageBeep()
            else:
                bad = st["stall"] or st["nolog"]
                recolor("#7a5a1d" if bad else ("#1d3a1d" if st["bot_on"] else "#3a3a3a"))
                head.config(text="%s %s  шаг %s/%s  убито %s" % ("БОТ" if st["bot_on"] else "бот стоит", st["zone"], st["step"], st["total"], st["kills"]))
            body.config(text="клетка %s | %s\nбез прогресса %s с | тишина лога %s с\n%s\n" % (st["vn"], st["hp"], st["idle_progress"], st["idle_log"], "\n".join(lines)))
        except Exception as e:
            body.config(text="ошибка наблюдателя: %r" % (e,))
        root.after(2000, loop)

    loop()
    root.mainloop()
    return 0


def main(argv):
    if len(argv) < 2:
        return gui()
    c = argv[1]
    if c == "wait":
        return cmd_wait(int(argv[2]) if len(argv) > 2 else 1500)
    if c == "status":
        print(json.dumps(json.load(open(STATUS, encoding="utf-8")), ensure_ascii=False) if os.path.exists(STATUS) else "нет status.json (окно не запущено)")
        return 0
    if c == "say":
        add_event("SAY", " ".join(argv[2:]))
        return 0
    if c == "call":
        open(CALL, "w", encoding="utf-8").write(" ".join(argv[2:]) or "готово")
        add_event("SAY", "ЗОВУ: " + " ".join(argv[2:]))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))


