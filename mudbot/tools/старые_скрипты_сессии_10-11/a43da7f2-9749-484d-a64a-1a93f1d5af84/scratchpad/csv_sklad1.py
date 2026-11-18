import re
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\склад1"
T = r"C:\Users\User\Desktop\Тадия\areas"
rows = open(REC + r"\склад1_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n")
orig = {r.split(";")[0].strip('"'): r.split(";") for r in open(REC + r"\рр_склад1V_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:] if r.strip()}
out = [r for r in rows if r.strip()]
snake = list(orig["Скользкая змея"]); snake[1] = '"Противная скользкая змея ползает тут. "'
out.append(";".join(snake))
open(T + r"\склад1_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
for r in out[1:]: print(r.split(";")[0], "|", r.split(";")[1])
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/крысы\\. Фу, какая мерзость\\./, /сюда забираться\\. Может, пора возвращаться\\./, /углам видны правильные сети паутины\\./, ")
open(q, "wb").write(s.encode("cp1251"))
t = open(r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js", "rb").read().decode("cp1251")
if '"склад1"' not in t:
    t = t.replace('"притон": "Притон"}', '"притон": "Притон", "склад1": "Склад в Геоланте"}').replace('{"притон": 1}', '{"притон": 1, "склад1": 1}')
    open(r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js", "wb").write(t.encode("cp1251"))
print("ok")
