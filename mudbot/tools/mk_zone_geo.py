"""Геолантская зона от склада р2 (115092) по СЫРОМУ логу пользователя и графу комнат: подход (BFS) + область + V-ходы зоны + возврат.

  python -X utf8 tools/mk_zone_geo.py <лог> <бот_имя> <vnum_клетки_создания> "<строка создания в логе>" <напр_области> [--end <vnum_возврата>]
пример: mk_zone_geo.py привы2 привы2 122011 "область создать в" в
Печатает: ходы зоны, невозможные ходы (граф неполный -> нужен прогон и tools/v_from_steps), клетки зоны до которых путь не дошёл.
csv не делает (tools/mob_lines_from_log.py + правка).
"""
import collections, json, os, re, sqlite3, sys, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
T = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\areas"
log_name, bot, start, create, dirn = sys.argv[1:6]
end = sys.argv[sys.argv.index("--end") + 1] if "--end" in sys.argv else start
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
INV = {v: k for k, v in RU.items()}
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): (z, n) for v, z, n in c.execute("select vnum,zone,name from rooms")}

def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    assert v == a, ("нет пути", a, b)
    return out[::-1]

log = open(os.path.join(JMC, log_name), "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(log) if l.strip().startswith(create))
cur, path, bad = start, [], []
for l in log[i0 + 1:]:
    s = SH.get(l.strip(), l.strip())
    if re.match(r"^(отпер|откр) \S+( \S+)?$", s):
        path.append((cur, "." + s))              # команда двери в текущей клетке
        continue
    if s in INV:
        nxt = R.get(cur, {}).get(INV[s])
        if nxt is None: bad.append((len(path), cur, s)); continue
        path.append((cur, s)); cur = str(nxt)
ends = [i for i, (v, m) in enumerate(path) if i > 0 and not m.startswith(".") and str(R[v][INV[m]]) == end]
cut = path[: ends[-1] + 1] if ends else path
first = next(str(R[v][INV[m]]) for v, m in cut if not m.startswith("."))
zone_ids = {v for v, (z, n) in N.items() if v[:3] == first[:3]}
seen = {v for v, _ in cut}
print("ходов зоны:", len(cut), "| невозможных в логе:", len(bad), bad[:6], "| клеток префикса %s: %d, посещено: %d" % (first[:3], len(zone_ids), len(seen & zone_ids)))
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
vl = lambda p: [(".триг " + V.format(v=v, c=m[1:])) if m.startswith(".") else V.format(v=v, c=m) for v, m in p]
appr = bfs("115092", start)
lines = [".триг #scr botCore.BotInZone = false"] + vl(appr) + [".триг обл с " + dirn] + vl(cut) + [".триг #scr botCore.BotInZone = false"] + vl(bfs(end, "115092"))
out = os.path.join(T, bot + ".botp")
if os.path.exists(out): shutil.copyfile(out, out + ".bak_geo")
open(out, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp:", out, "| строк", len(lines), "| подход", len(appr), "| индекс обл", 1 + len(appr))

