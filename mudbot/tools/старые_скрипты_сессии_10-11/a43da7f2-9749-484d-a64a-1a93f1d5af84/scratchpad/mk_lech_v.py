import re, shutil
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = max(i for i, l in enumerate(L) if "## BOT_START zone=леч" in l)
S = []
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\S*) cmd=(.*)$", l)
    if m: S.append((int(m.group(1)), m.group(2), m.group(3)))
MOVES = {"север", "юг", "восток", "запад", "вверх", "вниз"}
chain = []
for i, (idx, vn, cmd) in enumerate(S):
    nxt = S[i + 1][1] if i + 1 < len(S) else None
    inz = vn.startswith("182") or (vn == "180048" and cmd == "север" and not chain)
    if cmd in MOVES and inz and nxt is not None and nxt != vn:
        chain.append(("move", vn, cmd))
    elif cmd.startswith(".триг") and not cmd.startswith(".триг #") and vn.startswith("182"):
        chain.append(("cmd", vn, cmd))
last = max(i for i, (k, vn, c) in enumerate(chain) if k == "move" and vn.startswith("182"))
chain = chain[: last + 1]
print("элементов зоны:", len(chain), "| ходов:", sum(1 for k, _, _ in chain if k == "move"), "| последний:", chain[-1])
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
p = r"C:\Users\User\Desktop\Тадия\areas\леч.botp"
old = open(p, "rb").read().decode("cp1251").split("\r\n")
if old[-1] == "": old.pop()
area = next(i for i, l in enumerate(old) if l == ".триг обл с с")
exit_start = next(i for i, l in enumerate(old) if i > area and "== 180048} {юг}" in l and l.startswith("#if"))
print("индекс обл:", area, "| начало выхода:", exit_start, "| старых строк зоны:", exit_start - area - 1)
zone = [V.format(v=vn, c=c) if k == "move" else ".триг " + V.format(v=vn, c=c[len(".триг "):]) for k, vn, c in chain]
shutil.copyfile(p, p + ".bak_plain")
new = old[: area + 1] + zone + old[exit_start:]
open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("новых строк:", len(new))
