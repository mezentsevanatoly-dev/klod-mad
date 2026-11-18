import re, sqlite3, subprocess, time
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
names = {r[0] for r in c.execute("select name from rooms where vnum between 128001 and 128081")}
lines = set()
for i, l in enumerate(log):
    if not l.startswith("[ Exits"): continue
    j = i - 1; buf = []
    while j > i - 12 and log[j].strip() not in names:
        buf.append(log[j].rstrip()); j -= 1
    if log[j].strip() in names:
        for b in buf:
            if b.strip() and not re.search(r"^[\+\|:\-~ m%@]+$", b.strip()) and not re.search(r"\d+H \d+M", b): lines.add(b.strip())
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
def rx(l): return "/" + re.sub(r"([\\/.^$*+?()\[\]{}|-])", lambda m: "\\" + m.group(1), l) + "/"
lines = {l for l in lines if not l.startswith(("Труп", "[")) and len(l) > 4}
add = [rx(l) for l in lines if rx(l) not in s]
print("описаний:", len(lines), "новых в файл:", len(add))
j = s.index("];", s.index("InspectionWords"))
s = s[:j - 4] + ", ".join(add) + ", " + s[j - 4:]
open(p, "wb").write(s.encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
idx = 933; chunk = []; ln = 0
def flush():
    global chunk, idx
    if not chunk: return
    subprocess.run(J + ["#scr InspectionWords.splice(%d,0,%s)" % (idx, ",".join(chunk))], stdout=subprocess.DEVNULL); time.sleep(1.5)
    idx += len(chunk); chunk = []
for l in sorted(lines):
    r = "/" + re.sub(r"[\\/.^$*+?()\[\]{}|]", ".", l) + "/"
    if ln + len(r) > 600: flush(); ln = 0
    chunk.append(r); ln += len(r) + 1
flush()
print("индекс:", idx)
open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\idx.txt", "w").write(str(idx))
