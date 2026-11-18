import re, sqlite3, subprocess, time, glob, os
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
names = {r[0] for r in c.execute("select name from rooms where vnum between 135001 and 135999")}
root = r"C:\Users\User\Desktop\Клод мад"
files = [r"C:\Users\User\Desktop\Тадия\claude_game.log"] + glob.glob(root + r"\JMC\*") + glob.glob(root + r"\mudbot\data\recon\*\*")
lines = set()
for f in files:
    if not os.path.isfile(f) or os.path.getsize(f) > 80_000_000: continue
    raw = open(f, "rb").read()
    txt = raw.decode("cp1251", "replace")
    L = [re.sub(r"^\d\d:\d\d:\d\d ", "", x.replace("\r", "")) for x in txt.split("\n")]
    for i, l in enumerate(L):
        if not l.startswith("[ Exits"): continue
        j = i - 1; buf = []
        while j > i - 12 and L[j].strip() not in names:
            buf.append(L[j].rstrip()); j -= 1
        if j > i - 12 and L[j].strip() in names and L[j + 1].startswith("   "):
            for b in buf:
                b = b.strip()
                if b and not re.search(r"^[\+\|:\-~ m%@]+$", b) and not re.search(r"\d+H \d+M", b) and not b.startswith(("Труп", "[", "##", ">>")):
                    lines.add(b)
for f2 in glob.glob(r"C:\Users\User\Desktop\Тадия\areas\привы*_mob.csv"):
    for r in open(f2, "rb").read().decode("cp1251").split("\r\n")[1:]:
        q = r.split(";")
        if len(q) > 1: lines.add(q[1].strip('" '))
lines = {l for l in lines if l and len(l) > 4}
print("строк:", len(lines))
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
def rx(l): return "/" + re.sub(r"([\\/.^$*+?()\[\]{}|-])", lambda m: "\\" + m.group(1), l) + "/"
add = [rx(l) for l in lines if rx(l) not in s]
print("новых:", len(add))
j = s.index("];", s.index("InspectionWords"))
s = s[:j - 4] + ", ".join(add) + ", " + s[j - 4:]
open(p, "wb").write(s.encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
idx = int(open(S + r"\idx.txt").read()); chunk = []; ln = 0
def flush():
    global chunk, idx
    if not chunk: return
    subprocess.run(J + ["#scr InspectionWords.splice(%d,0,%s)" % (idx, ",".join(chunk))], stdout=subprocess.DEVNULL); time.sleep(1.5)
    idx += len(chunk); chunk = []
for l in sorted(l for l in lines if rx(l) in add):
    r = "/" + re.sub(r"[\\/.^$*+?()\[\]{}|]", ".", l) + "/"
    if ln + len(r) > 600: flush(); ln = 0
    chunk.append(r); ln += len(r) + 1
flush()
open(S + r"\idx.txt", "w").write(str(idx)); print("индекс", idx)
for x in ["#scr botCore.waitFlag=false", "#scr wTimerCount=0", "#scr jmc.killTimer(100)", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL)
