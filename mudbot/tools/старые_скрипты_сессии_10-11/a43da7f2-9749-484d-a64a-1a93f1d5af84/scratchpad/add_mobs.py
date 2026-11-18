import re, subprocess, time, os
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
root = r"C:\Users\User\Desktop\Клод мад\JMC"
files = [os.path.join(root, n) for n in ("рыбка", "кочи", "огис_конюшни", "геокаты2", "гоблины", "порт", "чайный_домик", "привы1", "привы2", "склад1", "склад2", "болото_часть", "канал", "каналгео1", "аллея", "парк", "притон", "ящеры", "огис_лечеб", "геоканал3", "церковь", "бесы", "храм", "луга", "луга2")] + [r"C:\Users\User\Desktop\Тадия\claude_game.log"]
lines = set()
for f in files:
    if not os.path.isfile(f) or os.path.getsize(f) > 90_000_000: continue
    L = [re.sub(r"^\d\d:\d\d:\d\d ", "", x.replace("\r", "")) for x in open(f, "rb").read().decode("cp1251", "replace").split("\n")]
    for i, l in enumerate(L):
        if not l.startswith("[ Exits"): continue
        j = i + 1
        while j < len(L) and L[j].strip() and not re.match(r"^\d+H \d+M", L[j].strip()) and j < i + 20:
            t = L[j].strip()
            if t and not t.startswith(("Труп", "[", "##", ">>")) and not re.search(r"(лежит|лежат) (тут|здесь)\.?( \[\d+\])?$", t) and len(t) > 6:
                lines.add(re.sub(r"\s*\[\d+\]$", "", re.sub(r"\s*\(\d+\)$", "", t)))
            j += 1
print("строк мобов/предметов:", len(lines))
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
def rx(l): return "/" + re.sub(r"([\\/.^$*+?()\[\]{}|-])", lambda m: "\\" + m.group(1), l) + "/"
add = [rx(l) for l in lines if rx(l) not in s]
print("новых:", len(add))
if add:
    j = s.index("];", s.index("InspectionWords"))
    s = s[:j - 4] + ", ".join(add) + ", " + s[j - 4:]
    open(p, "wb").write(s.encode("cp1251"))
    J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
    idx = int(open(S + r"\idx.txt").read()); chunk = []; ln = 0
    def flush():
        global chunk, idx
        if not chunk: return
        subprocess.run(J + ["#scr InspectionWords.splice(%d,0,%s)" % (idx, ",".join(chunk))], stdout=subprocess.DEVNULL); time.sleep(1.2)
        idx += len(chunk); chunk = []
    for l in sorted(l for l in lines if rx(l) in add):
        r = "/" + re.sub(r"[\\/.^$*+?()\[\]{}|]", ".", l) + "/"
        if ln + len(r) > 600: flush(); ln = 0
        chunk.append(r); ln += len(r) + 1
    flush()
    open(S + r"\idx.txt", "w").write(str(idx)); print("индекс", idx)
