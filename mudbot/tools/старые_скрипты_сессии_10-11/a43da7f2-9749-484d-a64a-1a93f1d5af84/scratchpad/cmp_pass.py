import re
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251").replace("\r", "").split("\n")
S = re.compile(r"^(\d\d:\d\d:\d\d) ## STEP (\d+) vn=(\S*) cmd=(.*)$")
runs, cur = [], None
for i, l in enumerate(L):
    m = S.match(l)
    if m and m.group(2) == "0":
        cur = []
        runs.append(cur)
    if m and cur is not None:
        cur.append((int(m.group(2)), m.group(3), m.group(4), m.group(1), i))
print("прогонов:", len(runs), [len(r) for r in runs])
a, b = runs[-3] if len(runs) >= 3 else runs[0], runs[-1]
# первый чистый прогон = тот, где 57 шагов (максимум)
clean = max(runs, key=len)
print("чистый:", len(clean), clean[0][3])
cm = {s[0]: s[1:3] for s in clean}
for s in runs[-1]:
    ref = cm.get(s[0])
    flag = "" if ref and ref[0] == s[1] and ref[1] == s[2] else "  <-- РАСХОЖДЕНИЕ, эталон %s" % (ref,)
    if flag or s[0] >= 16:
        print(s[3], s[0], s[1], s[2], flag)
# контекст последних строк перед расхождением
bad = next((s for s in runs[-1] if cm.get(s[0]) and cm[s[0]][0] != s[1]), None)
if bad:
    for l in L[bad[4] - 40: bad[4] + 2]:
        print("   ", l[:110])
