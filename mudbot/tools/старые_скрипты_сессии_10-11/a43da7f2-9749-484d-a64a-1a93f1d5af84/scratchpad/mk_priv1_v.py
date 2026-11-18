import re, json, sqlite3, collections, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}

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
    assert v == a, (a, b)
    return out[::-1]               # [(vnum_откуда, ход), ...]

L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = max(i for i, l in enumerate(L) if "## BOT_START zone=привы1" in l)
S = []
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\S*) cmd=(.*)$", l)
    if m: S.append((int(m.group(1)), m.group(2), m.group(3)))
MOVES = set(RU.values())
chain = []
for i, (idx, vn, cmd) in enumerate(S):
    nxt = S[i + 1][1] if i + 1 < len(S) else None
    inz = vn.startswith("122")
    if cmd in MOVES and inz and nxt is not None and nxt != vn:
        chain.append((vn, cmd))
print("ходов зоны по реальному проходу:", len(chain), "| последний:", chain[-1])
last_room = str(R[chain[-1][0]][{v: k for k, v in RU.items()}[chain[-1][1]]])
exit_path = bfs(last_room, "122011")
print("выход из", last_room, ":", len(exit_path), "ходов")
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
RUN = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
def sw(s):
    return [RUN[d] for n, d in re.findall(r"(\d*)([nsewud])", s) for _ in range(int(n) if n else 1)]
go = [m for _, m in bfs("115092", "115039")]
to_door = sw("9ne2ne2ne")
back_door = [OPP[m] for m in reversed(to_door)]
back = [m for _, m in bfs("115039", "115092")]
zone = [V.format(v=v, c=m) for v, m in chain + exit_path]
lines = [".триг #scr botCore.BotInZone = false"] + go + to_door + [".триг обл с в"] + zone + back_door + back
T = r"C:\Users\User\Desktop\Тадия\areas\привы1.botp"
shutil.copyfile(T, T + ".bak_r1")
open(T, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| путь к двери от склада р2:", go, "| обратно:", back)

