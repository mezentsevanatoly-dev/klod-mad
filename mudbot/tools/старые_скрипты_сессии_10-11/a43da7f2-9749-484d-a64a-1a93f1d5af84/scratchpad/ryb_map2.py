import re, collections
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\рыбка", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
st = 3005; end = 11893
rooms = collections.Counter()
for i in range(st, end):
    if log[i].startswith("[ Exits"):
        j = i + 1
        while j < len(log) and log[j].strip() and not re.match(r"^\d+H \d+M", log[j].strip()) and j < i + 16:
            t = log[j].strip()
            t = re.sub(r"(\s*\.\.\.[а-яё ]+)+\s*$", "", t)     # хвост аур
            t = re.sub(r"\s*\(\d+\)$", "", t)
            if t and not t.startswith(("Труп", "[", "Кучка", "-")) and t[-1] in ".!" and len(t) > 10 and "лежит" not in t:
                rooms[t] += 1
            j += 1
kills = collections.Counter()
for i in range(st, end):
    m = re.match(r"^(.+?) (мертв|мертва|мертвы)\. R\.I\.P\.", log[i].strip())
    if m and m.group(1) != "Кто-то": kills[m.group(1).strip()] += 1
def st4(w): return w.lower()[:4]
used = set()
for nm, n in kills.most_common():
    words = [st4(w) for w in re.findall(r"[А-Яа-яЁё]+", nm)]
    cands = [t for t in rooms if all(w in t.lower() for w in words)]
    if not cands:  # по последнему слову
        cands = [t for t in rooms if words and words[-1] in t.lower()]
    cands.sort(key=lambda t: -rooms[t])
    used.update(cands[:1])
    print("%-32s x%d | %s" % (nm, n, " || ".join("%s [x%d]" % (c[:72], rooms[c]) for c in cands[:2]) or "—"))
print("\nвсе строки зоны, которых нет выше (x>=1):")
for t, n in rooms.most_common():
    if t not in used: print("  x%-3d %s" % (n, t[:95]))
