import re, sqlite3, subprocess, time, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
names = {r[0] for r in c.execute("select name from rooms where vnum between 128001 and 128081")}
lines = set()
i = 1500
while i < 6830:
    t = log[i].strip()
    if t in names:
        j = i + 1; buf = []
        while j < len(log) and not log[j].startswith("[ Exits") and j < i + 14:
            buf.append(log[j].rstrip()); j += 1
        if j < len(log) and log[j].startswith("[ Exits"):
            for b in buf:
                if b.startswith("   ") or (b and not b.startswith(("[", "+", "|", ":")) and len(b) > 25 and not re.search(r"\d+H ", b)):
                    lines.add(b.strip())
        i = j
    i += 1
# мобы из csv
for r in open(r"C:\Users\User\Desktop\Тадия\areas\порт_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:]:
    p = r.split(";")
    if len(p) > 1: lines.add(p[1].strip('" ').strip())
lines = {l for l in lines if l and not l.startswith(("Труп", "Вы "))}
def rx(l):
    return "/" + re.sub(r"([\\/.^$*+?()\[\]{}|-])", lambda m: "\\" + m.group(1), l) + "/"
live = ["/" + l.replace("/", ".").replace("\\", ".") + "/" for l in lines]
live = ["/" + re.sub(r"[\\/.^$*+?()\[\]{}|]", ".", l) + "/" for l in lines]
print(len(lines))
# файл
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
add = [rx(l) for l in lines if rx(l) not in s]
j = s.index("];", s.index("InspectionWords"))
s = s[:j - 4] + ", ".join(add) + ", " + s[j - 4:]
open(p, "wb").write(s.encode("cp1251"))
print("в файл:", len(add))
# живой JMC
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
idx = 887; chunk = []; ln = 0
def flush():
    global chunk, idx
    if not chunk: return
    cmd = "#scr InspectionWords.splice(%d,0,%s)" % (idx, ",".join(chunk))
    subprocess.run(J + [cmd], stdout=subprocess.DEVNULL); time.sleep(1.5)
    idx += len(chunk); chunk = []
for r in sorted(live):
    if ln + len(r) > 600: flush(); ln = 0
    chunk.append(r); ln += len(r) + 1
flush()
print("живой индекс:", idx)
