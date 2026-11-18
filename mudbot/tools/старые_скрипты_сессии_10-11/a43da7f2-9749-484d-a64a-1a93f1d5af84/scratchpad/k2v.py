import re, json, collections
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = max(i for i, l in enumerate(L) if "## BOT_START zone=каты2пл" in l or "## AREA_NOWAIT" in l)
st = {}
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\S*) cmd=(.*)$", l)
    if m: st[int(m.group(1))] = (m.group(2), m.group(3).strip())
idx = sorted(k for k in st if k >= 13)
print("шагов", len(idx), idx[0], idx[-1])
MV = ("север", "юг", "восток", "запад", "вверх", "вниз")
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
out = []; bad = []
for a, k in enumerate(idx):
    vn, cmd = st[k]
    nxt = st[idx[a + 1]][0] if a + 1 < len(idx) else None
    if cmd in MV:
        if nxt == vn: bad.append((k, vn, cmd)); continue
        out.append(V.format(v=vn, c=cmd))
    elif cmd.startswith(".триг "):
        out.append(".триг " + V.format(v=vn, c=cmd[6:]))
    elif cmd.startswith(".пауза"):
        out.append(cmd)
print("потерянные/повторные:", bad[:10], "всего V:", len(out))
json.dump(out, open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\k2_v.json", "w", encoding="utf-8"), ensure_ascii=False)
print(st[13], st[14], st[idx[-1]])
