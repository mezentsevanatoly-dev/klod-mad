"""V-маршрут зоны из РЕАЛЬНОГО прохода: цепочка `## STEP idx vn=... cmd=...` в claude_game.log (vn = клетка, ИЗ которой ушла команда).

  python -X utf8 tools/v_from_steps.py <бот_имя> "<префикс vnum зоны, напр. 103>" <клетка_создания> [--since HH:MM:SS] [--dry]
Берёт шаги после последнего BOT_START (или --since), оставляет успешные ходы (следующий шаг начат в другой клетке), команды `.триг …`
сохраняет на месте; для зоны строит строки `#if {$MsdpRoomVnum != X} {...};#if {$MsdpRoomVnum == X} {ход}`.
Файл <бот_имя>.botp = старое начало до строки «.триг обл …» (включительно) + V-часть зоны + дорога обратно из клетки создания по графу БД
(старое — в .bak_v). --dry: только показать.
"""
import collections, json, os, re, shutil, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\areas"
LOG = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log"
bot, pref, start = sys.argv[1:4]
since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None
MOVES = {"север", "юг", "восток", "запад", "вверх", "вниз"}
L = open(LOG, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = 0
for i, l in enumerate(L):
    if "## BOT_START" in l and (since is None):
        b = i
    if since and re.match(r"^%s" % re.escape(since[:5]), l) and b == 0:
        b = i
S = []
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\S*) cmd=(.*)$", l)
    if m: S.append((int(m.group(1)), m.group(2), m.group(3)))
    if "## ZONE_END" in l: break
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
zone = []
for i, (idx, vn, cmd) in enumerate(S):
    nxt = S[i + 1][1] if i + 1 < len(S) else None
    inz = vn.startswith(pref) or (vn == start and cmd == "север")
    if cmd in MOVES:
        if inz and nxt is not None and nxt != vn:
            zone.append(("move", vn, cmd))
    elif cmd.startswith(".триг") and not cmd.startswith(".триг #scr") and "обл" not in cmd and vn.startswith(pref):
        zone.append(("cmd", vn, cmd))
# конец: последний выход (первая клетка зоны -> start)
last = max((i for i, (k, vn, c) in enumerate(zone) if k == "move" and vn.startswith(pref)), default=None)
zone = zone[: last + 1] if last is not None else zone
print("ходов/команд зоны:", len(zone))
for k, vn, c in zone:
    print("  ", k, vn, c)
if "--dry" in sys.argv:
    sys.exit(0)
db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {str(v): json.loads(e or "{}") for v, e in db.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
q = collections.deque([start]); p = {start: None}
while q:
    v = q.popleft()
    if v == "100076": break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in p and t in R: p[t] = (v, d); q.append(t)
back = []; v = "100076"
while p[v]: v, d = p[v][0], p[v][1]; back.append(RU[d])
back = back[::-1]
path = os.path.join(A, bot + ".botp")
old = open(path, "rb").read().decode("cp1251").split("\r\n")
cut = max(i for i, l in enumerate(old) if l.startswith(".триг обл"))
shutil.copyfile(path, path + ".bak_v")
new = old[: cut + 1] + [(V.format(v=vn, c=c) if k == "move" else c) for k, vn, c in zone] + back
open(path, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("записано", path, "| строк", len(new), "| дорога назад", len(back))
