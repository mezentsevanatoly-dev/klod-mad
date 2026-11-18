REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\привы2"
T = r"C:\Users\User\Desktop\Тадия\areas"
rows = [r for r in open(REC + r"\привы2_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n") if r.strip()]
orig = {r.split(";")[0].strip('"'): r.split(";") for r in open(REC + r"\рр_привы2V_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:] if r.strip()}
t = list(orig["Любопытная трясогузка"]); t[1] = '"Необычайно любопытная трясогузка рассматривает вас. "'
rows.append(";".join(t))
open(T + r"\привы2_mob.csv", "wb").write(("\r\n".join(rows) + "\r\n").encode("cp1251"))
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/из неловких пришельцев\\./, /ветвями винограда\\./, /Кучка монет лежит здесь\\./, ")
open(q, "wb").write(s.encode("cp1251"))
g = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t2 = open(g, "rb").read().decode("cp1251")
if '"привы2"' not in t2:
    t2 = t2.replace('"каты1": "Катакомбы Геоланта"}', '"каты1": "Катакомбы Геоланта", "привы2": "Дом с привидениями"}').replace('"каты1": 1}', '"каты1": 1, "привы2": 1}')
    open(g, "wb").write(t2.encode("cp1251"))
print("csv", len(rows) - 1, "ok")
