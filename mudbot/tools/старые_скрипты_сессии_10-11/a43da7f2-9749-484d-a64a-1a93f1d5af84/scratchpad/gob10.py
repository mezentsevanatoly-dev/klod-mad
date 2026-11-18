import shutil, subprocess, time, collections, json, sqlite3
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\gob2.py", encoding="utf-8").read().split('print("команд"')[0])
p = r"C:\Users\User\Desktop\Тадия\areas\гоблины.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
shutil.copyfile(p, p + ".bak_loop")
head = L[:69]                                   # до начала похода на запад
RUm = {"N": "север", "S": "юг", "E": "восток", "W": "запад"}
west = ["запад"] * 4 + ["север", "запад", "запад", "запад"] + ["север", "запад", "запад", "восток", "восток", "юг"]
back = ["восток", "восток", "восток", "юг", "восток", "восток", "восток", "восток"]   # 127005 -> 108023
part2 = ["юг"] * 6 + [it[0] for it in items[101:124]]
cmds_check = west + back
# проверка по графу из 108023 на запад
cur = "108023"
for c_ in west + back + part2:
    t = R.get(cur, {}).get(INV[c_])
    if t is None: print("НЕТ ХОДА", cur, c_); break
    cur = str(t)
print("конец:", cur, NM.get(cur))
tail_start = len(head) + len(west) + len(back)
back_home = L[-6:] if False else None
# возврат домой: берём последние строки старого файла (BFS 122047->115092) - они помечены BotInZone=false
i_false = max(k for k, x in enumerate(L) if x == ".триг #scr botCore.BotInZone = false")
home = L[i_false:]
new = head + west + back + part2 + home
open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("строк", len(new), "старт части 2 (юг x5 от 108022): строка", tail_start + 1)
json.dump(tail_start + 1, open(S + r"\gob_resume.json", "w"))
