"""Зона для JMC-бота целиком из СЫРОГО лога пользователя и графа комнат (зоны с областью, старт в городе).

  python -X utf8 tools/mk_zone_raw.py <лог> <бот_имя> <vnum_клетки_создания> "<строка создания в логе>" <напр> <имя_зоны_в_БД>
пример: mk_zone_raw.py притон притон 100011 "область создать с" с Притон
Результат: Тадия\\areas\\<бот_имя>.botp = [BotInZone=false] + дорога от склада 100076 + «.триг обл с <напр>» + V-ходы по логу
           (обрезаны на последнем возврате в клетку создания) + дорога обратно; csv НЕ делает (tools/mob_lines_from_log.py).
Печатает: ходы, невозможные ходы, клетки зоны, до которых путь не дошёл.
"""
import collections, json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
T = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\areas"
log_name, bot, start, create, dirn, zone = sys.argv[1:7]
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
RU = {v: k for k, v in D.items()}
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = {str(v) for v, z in c.execute("select vnum,zone from rooms") if z == zone}

def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v):
        pv, d = p[v]; out.append(RU[d]); v = pv
    assert v == a, (a, b)
    return out[::-1]

log = open(os.path.join(JMC, log_name), "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(log) if l.strip().startswith(create))
cur, path, bad = start, [], []
for l in log[i0 + 1:]:
    s = SH.get(l.strip(), l.strip())
    if s in D:
        nxt = R.get(cur, {}).get(D[s])
        if nxt is None: bad.append((len(path), cur, s)); continue
        path.append((cur, s)); cur = str(nxt)
# обрезка: последний ход, после которого мы снова в клетке создания
ends = []
cur = start
for i, (v, m) in enumerate(path):
    nxt = str(R[v][D[m]])
    if nxt == start and i > 0: ends.append(i)
cut = path[: ends[-1] + 1] if ends else path
seen = {v for v, _ in cut}
print("ходов в зоне:", len(cut), "| отброшен хвост:", len(path) - len(cut), "| невозможных ходов в логе:", len(bad), bad[:5])
print("клеток зоны в БД:", len(Z), "| не тронуто:", [(v, N[v]) for v in sorted(Z - seen, key=int)][:15])
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
lines = [".триг #scr botCore.BotInZone = false"] + bfs("100076", start) + [".триг обл с " + dirn] + [V.format(v=v, c=m) for v, m in cut] + bfs(start, "100076")
open(os.path.join(T, bot + ".botp"), "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
json.dump(cut, open(os.path.join(ROOT, "data", "recon", log_name + "_cut.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("записано:", os.path.join(T, bot + ".botp"), "| строк", len(lines))
