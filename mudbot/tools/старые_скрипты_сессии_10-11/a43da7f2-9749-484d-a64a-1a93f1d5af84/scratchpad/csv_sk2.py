REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\склад2"
T = r"C:\Users\User\Desktop\Тадия\areas"
rows = [r for r in open(REC + r"\склад2_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n") if r.strip()]
out = [r for r in rows if "копошится" not in r and "ходит тут между стеллажей" not in r]
open(T + r"\склад2_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/связываться\\./, ")
open(q, "wb").write(s.encode("cp1251"))
g = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t2 = open(g, "rb").read().decode("cp1251")
if '"склад2"' not in t2:
    t2 = t2.replace('"привы2": "Дом с привидениями"}', '"привы2": "Дом с привидениями", "склад2": "Склад в Геоланте"}').replace('"привы2": 1}', '"привы2": 1, "склад2": 1}')
    open(g, "wb").write(t2.encode("cp1251"))
print("csv", len(out) - 1)
