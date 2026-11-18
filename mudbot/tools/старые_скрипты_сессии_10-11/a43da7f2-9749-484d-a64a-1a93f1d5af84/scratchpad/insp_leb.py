q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/Огис кажется неприступным\\./, /Угрюмый погонщик запрягает в телегу тощую лошадку\\./, /свой товар прохожим\\./, /из палат\\./, /^формы\\.$/, ")
open(q, "wb").write(s.encode("cp1251"))
print("ok")
