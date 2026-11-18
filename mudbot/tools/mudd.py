"""mudd — мой собственный клиент: держит соединение с игрой и отдаёт управление через localhost-порт.

Запуск (в отдельном окне консоли, логин и пароль вводит ЧЕЛОВЕК прямо в этом окне):
    python -X utf8 tools/mudd.py [--host sowmud.ru] [--port 5555] [--api 5599] [--triggers triggers.txt|none]
Дальше я работаю через tools/mc.py (send/tail/status/wait). Окно показывает игру, как JMC, и принимает ввод человека.

Консольные команды человека: /ok (проверка присутствия пройдена), /known, /reload, /кон (переподключиться), /quit.
Безопасность: пока не вошли в игру или сработал детектор проверки присутствия, API команды в игру не отправляет;
сбросить тревогу может только человек в этом окне (/ok).
"""
import argparse
import collections
import json
import os
import re
import socketserver
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from mudbot.client import Client      # noqa: E402
from mudbot.parser import parse_status  # noqa: E402

CTL = os.path.join(ROOT, "ctl.txt")   # кнопки tools/alarm_popup.py: /ok, /known


class Hub:
    """Кольцевой буфер строк игры с номерами: любой клиент API читает «всё после номера N»."""

    def __init__(self, client):
        self.c = client
        self.buf = collections.deque(maxlen=30000)
        self.seq = 0
        self.cond = threading.Condition()
        self.status = None            # последний разобранный промпт
        self.status_t = 0.0
        self.send_lock = threading.Lock()
        threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self):
        while True:
            try:
                ln = self.c.lines.get(timeout=1)
            except Exception:
                continue
            st = parse_status(ln.text)
            with self.cond:
                self.seq += 1
                self.buf.append((self.seq, ln.t, ln.text))
                if st:
                    self.status, self.status_t = st, ln.t
                self.cond.notify_all()

    def since(self, seq):
        with self.cond:
            return [(s, t, x) for s, t, x in self.buf if s > seq]

    def wait_quiet(self, seq, quiet, until, limit):
        """Ждать, пока игра не замолчит на quiet сек (или не встретится until, или не пройдёт limit сек)."""
        pat = re.compile(until) if until else None
        end = time.time() + limit
        last = time.time()
        seen = seq
        while time.time() < end:
            with self.cond:
                self.cond.wait(timeout=0.1)
                fresh = [(s, t, x) for s, t, x in self.buf if s > seen]
            if fresh:
                seen = fresh[-1][0]
                last = time.time()
                if pat and any(pat.search(x) for _, _, x in fresh):
                    time.sleep(0.15)          # дочитать хвост
                    break
            elif time.time() - last >= quiet:
                break
        return self.since(seq)

    def state(self):
        c = self.c
        st = self.status
        return {
            "connected": c.alive.is_set(), "logged_in": c.logged_in.is_set(),
            "alarm": c.presence_alarm.is_set(), "odd": list(getattr(c.presence, "last_odd", []))[-5:],
            "seq": self.seq,
            "prompt": None if not st else {"hp": st.hp, "mp": st.mp, "mv": st.mv, "gold": st.gold, "exits": st.exits,
                                           "in_battle": st.in_battle, "foe": st.foe, "age": round(time.time() - self.status_t, 1)},
            "room": {k: c.msdp_room.get(k) for k in ("VNUM", "AREA", "NAME", "EXITS")} if c.msdp_room else None,
        }


def handle(hub, req):
    op = req.get("op")
    c = hub.c
    if op == "status":
        return {"ok": True, **hub.state()}
    if op == "tail":
        rows = list(hub.buf)[-int(req.get("n", 40)):]
        return {"ok": True, "seq": hub.seq, "lines": [x for _, _, x in rows]}
    if op == "read":                                    # {since: seq, quiet, until, max}
        seq = int(req.get("since", hub.seq))
        rows = hub.wait_quiet(seq, float(req.get("quiet", 0)), req.get("until"), float(req.get("max", 0.01)))
        return {"ok": True, "seq": hub.seq, "lines": [x for _, _, x in rows]}
    if op == "send":                                    # {cmds: [...], gap, quiet, until, max}
        if not c.alive.is_set():
            return {"ok": False, "error": "нет соединения с игрой (человек: /кон)"}
        if not c.logged_in.is_set():
            return {"ok": False, "error": "ещё не вошли в игру: логин и пароль вводит человек в окне mudd"}
        if c.presence_alarm.is_set():
            return {"ok": False, "error": "ТРЕВОГА проверки присутствия: отвечает человек (молиться …), потом /ok в окне mudd"}
        with hub.send_lock:                              # пакеты разных вызовов не перемешиваются
            seq = hub.seq
            gap = float(req.get("gap", 0.25))
            for cmd in req.get("cmds", []):
                if c.presence_alarm.is_set():
                    return {"ok": False, "error": "тревога посреди пакета", "seq": seq}
                c.send(cmd)
                time.sleep(gap)
            rows = hub.wait_quiet(seq, float(req.get("quiet", 1.0)), req.get("until"), float(req.get("max", 30)))
        return {"ok": True, "seq": hub.seq, "lines": [x for _, _, x in rows], "state": hub.state()}
    return {"ok": False, "error": f"неизвестная операция {op!r}"}


def serve(hub, port):
    class H(socketserver.StreamRequestHandler):
        def handle(self):
            for raw in self.rfile:
                try:
                    resp = handle(hub, json.loads(raw.decode("utf-8")))
                except Exception as e:              # не ронять демон из-за одного запроса
                    resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
                self.wfile.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    srv = S(("127.0.0.1", port), H)            # только localhost
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ctl_lines(state):
    try:
        with open(CTL, encoding="utf-8") as f:
            f.seek(state["pos"])
            data = f.read()
            state["pos"] = f.tell()
    except FileNotFoundError:
        return []
    return data.split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="sowmud.ru")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--api", type=int, default=5599)
    ap.add_argument("--triggers", default="none", help="файл триггеров в папке mudbot или none")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    open(CTL, "a").close()
    ctl = {"pos": os.path.getsize(CTL)}
    logdir = os.environ.get("MUDD_LOGDIR", ROOT)          # для тестов на фейковом сервере
    c = Client(host=a.host, port=a.port, raw_log=os.path.join(logdir, "raw.log"), text_log=os.path.join(logdir, "out.log"),
               known_path=os.path.join(ROOT, "presence_known.txt"))
    if a.triggers != "none":
        c.load_triggers(os.path.join(ROOT, a.triggers))
    c.connect()
    hub = Hub(c)
    serve(hub, a.api)
    print(f"[mudd] подключено к {a.host}:{a.port}, API 127.0.0.1:{a.api}. Логин и пароль вводите здесь сами.", flush=True)
    while True:
        for line in ctl_lines(ctl):
            if line.strip() in ("/ok", "/known"):
                c.commands.put(line.strip())
        try:
            cmd = c.commands.get(timeout=0.3)
        except Exception:
            if not c.alive.is_set():
                time.sleep(0.5)
            continue
        if cmd in ("/known", "/лтщцт"):
            c.presence.add_known(c.presence.last_odd)
            c.presence_alarm.clear()
            c.presence.recent.clear()
            print("[mudd] строки запомнены как обычные, продолжаю", flush=True)
        elif cmd in ("/ok", "/ок"):
            c.presence_alarm.clear()
            c.presence.recent.clear()
            print("[mudd] тревога снята, продолжаю", flush=True)
        elif cmd in ("/reload", "/кудщфв") and a.triggers != "none":
            c.load_triggers(os.path.join(ROOT, a.triggers))
        elif cmd == "/кон":
            print("[mudd] переподключение, потом снова логин и пароль", flush=True)
            c.reconnect()


if __name__ == "__main__":
    main()
