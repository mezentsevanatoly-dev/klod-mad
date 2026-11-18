import re, collections
R = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\аллея"
L = open(R + r"\рр_аллеяV.botp", "rb").read().decode("cp1251").splitlines()
print("строк", len(L))
for i, l in enumerate(L[:14]):
    m = re.search(r"== (\d+)\} \{(.*)\}$", l)
    print(i, (m.group(1), m.group(2)) if m else l)
print("...")
for i, l in enumerate(L[-6:], len(L) - 6):
    m = re.search(r"== (\d+)\} \{(.*)\}$", l)
    print(i, (m.group(1), m.group(2)) if m else l)
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\аллея", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
print("лог строк", len(log))
kills = collections.Counter()
for l in log:
    m = re.match(r"^(.+?) (?:мертв[аоы]?)\. R\.I\.P\.", l)
    if m: kills[m.group(1)] += 1
print("убийства:", dict(kills))
# строки мобов: между «[ Exits» и промптом
mob = collections.Counter()
for i, l in enumerate(log):
    if l.startswith("[ Exits"):
        j = i + 1
        while j < len(log) and not re.match(r"^\d+H \d+M", log[j]) and j < i + 15:
            s = log[j].strip()
            if s and not s.startswith("Труп") and "лежит" not in s[-12:]:
                mob[s] += 1
            j += 1
for s, n in mob.most_common(60):
    print(n, s[:110])
