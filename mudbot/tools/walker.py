# -*- coding: utf-8 -*-
"""Спидволк А<->Б с добором: пачки по 14 ходов через ';', после каждой пачки сверка клетки (ClaudeLog.note + MSDP), остаток пути пересчитывается от
текущей клетки по графу game.db. Бой/агро-мобы по дороге (пиявки): ждёт конец боя и добирает. Используется надсмотрщиком (inc_supervisor.run_zone)."""
import os, re, time, json, sqlite3, subprocess, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
_G = {}


def graph():
    if not _G:
        c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
        for v, e in c.execute("select vnum,exits from rooms"):
            try:
                _G[str(v)] = {d: str(t) for d, t in json.loads(e or "{}").items()}
            except Exception:
                _G[str(v)] = {}
    return _G


def bfs(src, dst):
    G = graph(); prev = {src: None}; q = collections.deque([src])
    while q:
        v = q.popleft()
        if v == dst:
            break
        for d, t in G.get(v, {}).items():
            if t not in prev:
                prev[t] = (v, d); q.append(t)
    if dst not in prev:
        return None
    out = []; v = dst
    while prev[v]:
        p, d = prev[v]; out.append(RU[d]); v = p
    out.reverse()
    return out


class Jaba:
    def __init__(self, folder):
        self.dir = os.path.join(BASE, folder); self.log = os.path.join(self.dir, "claude_game.log")
        self.env = dict(os.environ, JMC_TARGET=self.dir)

    def send(self, cmd, w=1.0):
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "do", "--force", cmd, str(w)], env=self.env, capture_output=True)

    def tail(self, pos):
        return open(self.log, "rb").read()[pos:].decode("cp1251", "replace")

    def vnum(self):
        pos = os.path.getsize(self.log); self.send("#scr ClaudeLog.note('VN=' + $MsdpRoomVnum)", 1.5)
        m = re.findall(r"## VN=(\d+)", self.tail(pos))
        return m[-1] if m else None


def walk(folder, dst, chunk=80, say=print, max_rounds=40):
    """Довести персонажа жабы до клетки dst. True/False."""
    j = Jaba(folder); dst = str(dst)
    for rnd in range(max_rounds):
        cur = j.vnum()
        if cur is None:
            time.sleep(2); continue
        if cur == dst:
            return True
        path = bfs(cur, dst)
        if not path:
            say("walker: нет пути %s -> %s" % (cur, dst)); return False
        pack = path[:chunk]
        pos = os.path.getsize(j.log); j.send(";".join(pack), 1.0)
        time.sleep(0.25 * len(pack) + 1.0)
        new = j.tail(pos)
        if "слишком устали" in new:
            time.sleep(5)
        if re.search(r"Не получится! Вы сражаетесь|сражаетесь за свою жизнь|вступил в бой|Очередь команд очищена", new):
            time.sleep(2)                      # бой/агро (пиявки): дать добить и добрать остаток
        if re.search(r"заперт|Закрыто", new) and not re.search(r"не заперт", new):
            say("walker: дверь на пути (%s)" % ";".join(pack)); return False
    say("walker: не дошёл за %d кругов" % max_rounds); return False


if __name__ == "__main__":
    print("OK" if walk(sys.argv[1], sys.argv[2]) else "FAIL")
