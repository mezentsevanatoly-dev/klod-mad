# -*- coding: utf-8 -*-
"""Отвести персонажа жабы в комнату по графу game.db: python tools/walk_to.py <папка жабы> <vnum цель>. Берёт текущую клетку через ClaudeLog.note, BFS, ходы по одному; стоп при «Вы не можете»."""
import os, re, sys, time, json, sqlite3, subprocess, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
jaba, dst = sys.argv[1], sys.argv[2]
env = dict(os.environ, JMC_TARGET=os.path.join(BASE, jaba))
log = os.path.join(BASE, jaba, "claude_game.log")
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}


def jmc(cmd, w=1.0):
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "do", "--force", cmd, str(w)], env=env, capture_output=True)


def tail_from(pos):
    b = open(log, "rb").read()
    return b[pos:].decode("cp1251", "replace")


pos = os.path.getsize(log)
jmc("#scr ClaudeLog.note('VN=' + $MsdpRoomVnum)", 1.5)
m = re.findall(r"## VN=(\d+)", tail_from(pos))
if not m:
    raise SystemExit("клетка не определена")
src = m[-1]; print("из", src, "в", dst, flush=True)
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db")); G = {}
for v, e in c.execute("select vnum,exits from rooms"):
    try:
        G[str(v)] = {d: str(t) for d, t in json.loads(e or "{}").items()}
    except Exception:
        G[str(v)] = {}
prev = {src: None}; q = collections.deque([src])
while q:
    v = q.popleft()
    if v == dst:
        break
    for d, t in G.get(v, {}).items():
        if t not in prev:
            prev[t] = (v, d); q.append(t)
if dst not in prev:
    raise SystemExit("нет пути")
path = []; v = dst
while prev[v]:
    p, d = prev[v]; path.append(RU[d]); v = p
path.reverse(); print("шагов", len(path), flush=True)
CH = 14                                    # спидволк: пачки по 14 ходов через ';' одной командой
for i in range(0, len(path), CH):
    pack = path[i:i + CH]
    pos = os.path.getsize(log); jmc(";".join(pack), 1.0)
    time.sleep(0.25 * len(pack) + 1.0)
    new = tail_from(pos)
    if "слишком устали" in new:
        time.sleep(5)
    if re.search(r"Вы не можете идти|Закрыто|заперт", new):
        print("ПРЕРВАНО в пачке", i // CH + 1, ";".join(pack)); sys.exit(2)
print("дошёл:", dst)