import json, sqlite3, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
import resolve_entries as RE
R = RE.R
st = json.load(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы\бесы_route.json", encoding="utf-8"))["steps"]
k = next(i for i, s in enumerate(st) if s.get("cmd", "").startswith("область создать"))
pre = [s for s in st[:k] if "move" in s]
print("шагов", len(pre), "первые комнаты:", [s["room"] for s in pre[:5]], "последние:", [s["room"] for s in pre[-4:]])
D = RE.D
# перебор стартов: любая комната Элендора, с которой ходы бесов проходят с ≤3 пропусками
best = []
for v, (z, n, e) in R.items():
    if "Элендор" not in z:
        continue
    r = RE.walk(v, pre, maxskip=3)
    if r:
        best.append((r[2], v, n, r[0], R[r[0]][1], R[r[0]][0]))
best.sort()
print(best[:5])
