import re, collections
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\рыбка", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
st = 3005; end = 11893
# строки мобов в комнатах зоны
rooms = collections.Counter()
for i in range(st, end):
    if log[i].startswith("[ Exits"):
        j = i + 1
        while j < len(log) and log[j].strip() and not re.match(r"^\d+H \d+M", log[j].strip()) and j < i + 14:
            t = log[j].strip()
            if t and not t.startswith(("Труп", "[", "Кучка монет", "Вы ", "-")) and re.search(r"[.!]$", t) and len(t) > 12 and not re.search(r"(лежит|лежат|стоит) здесь\.$", t.replace("стоит здесь", "лежит здесь")) is None:
                rooms[re.sub(r"\s*\(\d+\)$", "", t)] += 1
            j += 1
kills = collections.Counter()
for i in range(st, end):
    m = re.match(r"^(.+?) (мертв|мертва|мертвы)\. R\.I\.P\.", log[i].strip())
    if m and m.group(1) != "Кто-то": kills[m.group(1).strip()] += 1
def stem(w): return w.lower()[:5]
out = []
for nm in kills:
    words = [stem(w) for w in re.findall(r"[А-Яа-яЁё]+", nm)]
    cands = [t for t in rooms if all(w in t.lower() for w in words)] or [t for t in rooms if words and words[-1] in t.lower()]
    cands.sort(key=lambda t: -rooms[t])
    out.append((nm, kills[nm], cands[:2]))
for nm, n, c in out: print("%-32s x%d | %s" % (nm, n, " || ".join(x[:70] for x in c) if c else "— строки комнаты не найдено"))
print("\nмобы-строки зоны, не попавшие ни к одному убитому:")
used = {x for _, _, c in out for x in c}
for t, n in rooms.most_common():
    if t not in used and n >= 1 and len(t) < 90: print("  x%-3d %s" % (n, t))
