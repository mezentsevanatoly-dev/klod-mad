import sqlite3, re
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
n = sorted({r[0] for r in c.execute("select name from rooms where vnum between 128001 and 128081")})
print(n)
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
add = [x for x in n if re.fullmatch(r"[А-Яа-яЁё ,\-]+", x) and ("/^" + x + "$/") not in s]
rx_file = ["/^" + x + "$/" for x in add] + [r"/голодных жителей\./"]
rx_live = ["/^" + x + "$/" for x in add] + ["/голодных жителей./"]
j = s.index("];", s.index("InspectionWords"))
s = s[:j - 4] + ", ".join(rx_file) + ", " + s[j - 4:]
open(p, "wb").write(s.encode("cp1251"))
live = "#scr InspectionWords.splice(InspectionWords.length-1,0," + ",".join(rx_live) + ")"
open(S + r"\live2.txt", "w", encoding="utf-8").write(live)
print(len(rx_live))
