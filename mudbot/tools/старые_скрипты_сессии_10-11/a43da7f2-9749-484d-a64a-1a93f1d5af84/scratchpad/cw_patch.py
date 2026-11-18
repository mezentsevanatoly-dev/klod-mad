p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\chainwatch.py"
s = open(p, encoding="utf-8").read()
if "def zone_by_total" not in s:
    s = s.replace("pos = os.path.getsize(LOG);", '''def zone_by_total(total, hint):
    cand = []
    for fn in os.listdir(AREAS):
        if fn.endswith(".botp"):
            try:
                n = len([x for x in open(os.path.join(AREAS, fn), "rb").read().decode("cp1251").split("\\r\\n") if x != ""])
            except Exception: continue
            if n == total: cand.append(fn[:-5])
    if hint in cand or len(cand) != 1: return hint if hint in cand else (cand[0] if len(cand) == 1 else None)
    return cand[0]

pos = os.path.getsize(LOG);''', 1)
    s = s.replace('''        n = int(m.group(1)); buf = ""''', '''        n = int(m.group(1)); buf = ""
        zone = zone_by_total(int(m.group(2)), zone) or zone''', 1)
open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("ok")
