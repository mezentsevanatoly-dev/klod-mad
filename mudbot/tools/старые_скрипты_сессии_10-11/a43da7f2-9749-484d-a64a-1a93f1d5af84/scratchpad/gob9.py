import collections, json
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\gob2.py", encoding="utf-8").read().split('print("команд"')[0])
cur = "122047"; out = []; bad = []
for n in range(32, 124):
    cmd, name, ex, li = items[n]
    if cmd not in MV: out.append((cur, "." + cmd)); continue
    t = R.get(cur, {}).get(INV[cmd])
    if t is None:
        bad.append((n, cur, NM.get(cur), cmd, name)); out.append((cur, cmd, "FAIL")); continue
    nn = NM.get(str(t))
    if name and name != nn and not name.startswith("Здесь темно"): bad.append((n, cur, cmd, "граф:", nn, "лог:", name))
    out.append((cur, cmd)); cur = str(t)
print("конец", cur, NM.get(cur), "| расхождений:", len(bad))
for b in bad[:30]: print(b)
json.dump(out, open(S + r"\gob_full.json", "w", encoding="utf-8"), ensure_ascii=False)
