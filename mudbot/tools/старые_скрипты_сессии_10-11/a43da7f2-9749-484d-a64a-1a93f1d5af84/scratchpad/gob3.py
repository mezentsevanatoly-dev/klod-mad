import re, json, sqlite3, collections
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\gob2.py", encoding="utf-8").read().split("json.dump")[0])
byname = collections.defaultdict(list)
for v, n in NM.items(): byname[n].append(v)
OPPD = OPP
# 35 ходов до дороги, 36-й 'юг' в лагерь
mv = [it for it in items]
road = [it[0] for it in mv[:35]]
print("дорога:", road)
cur = "122047"; out = []; amb = []; fixes = 0
for n, (cmd, name, ex, li) in enumerate(mv[35:], 35):
    if cmd not in MV: out.append((cur, "." + cmd)); continue
    d = INV[cmd]; t = R.get(cur, {}).get(d)
    if t is not None and (name is None or NM.get(str(t)) == name):
        out.append((cur, cmd)); cur = str(t); continue
    cands = [v for v in byname.get(name, []) if v in Z and (ex is None or set(R[v].keys()) == ex)]
    if len(cands) > 1:
        c2 = [v for v in cands if R[v].get(OPP[d]) == cur]
        if c2: cands = c2
    out.append((cur, cmd))
    if len(cands) == 1: cur = cands[0]; fixes += 1; R[out[-1][0]][d] = int(cur)
    else:
        amb.append((n, out[-1][0], cmd, name, ex, cands))
        if cands: cur = cands[0]
print("camp шагов:", len(out), "исправлений:", fixes, "неясных:", len(amb)); [print(a) for a in amb[:12]]
print("конец:", cur, NM.get(cur)); Zs = set(Z); seen = {v for v, _ in out}
print("клеток зоны", len(Zs), "посещено", len(seen & Zs))
json.dump(out, open(S + r"\gob_camp.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(road, open(S + r"\gob_road.json", "w", encoding="utf-8"), ensure_ascii=False)
