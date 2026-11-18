import collections, json
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\gob2.py", encoding="utf-8").read().split('print("команд"')[0])
cur = "108022"
cmds = ["юг"] * 5 + [it[0] for it in items[101:124]]
out = []
for k, cmd in enumerate(cmds):
    t = R.get(cur, {}).get(INV[cmd])
    nm = items[100 + k][1] if k >= 5 else None
    print(k, cur, NM.get(cur), cmd, "->", t, NM.get(str(t)) if t else None, "| лог:", nm)
    if t is None: print("НЕТ ХОДА"); break
    out.append((cur, cmd)); cur = str(t)
print("конец", cur, NM.get(cur))
json.dump(out, open(S + r"\gob_rest.json", "w", encoding="utf-8"), ensure_ascii=False)
