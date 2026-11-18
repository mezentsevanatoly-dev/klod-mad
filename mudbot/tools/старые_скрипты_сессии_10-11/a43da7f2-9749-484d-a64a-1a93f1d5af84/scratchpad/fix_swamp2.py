p = r"C:\Users\User\Desktop\Тадия\areas\болото.botp"
import shutil
shutil.copyfile(p, p + ".bak_road")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "":
    L.pop()
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}
t1 = L.index(".триг #scr botCore.BotInZone = true")
go = L[1:t1]                                   # 31 ход от склада; в игре приводит в 104044, а не в 104043
t2 = max(i for i, l in enumerate(L) if l.startswith("#if"))
mid = L[t1:t2 + 1]                             # BotInZone=true + V-ходы болота
tail_flag = L[t2 + 1]
assert tail_flag.startswith(".триг #scr botCore.BotInZone = false"), tail_flag
back = ["запад"] + [OPP[m] for m in reversed(go)]
new = [L[0]] + go + ["восток"] + mid + [tail_flag] + back
open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("строк", len(new), "| восток вставлен на индексе", 1 + len(go), "| обратно", len(back), back[:4], "...")
