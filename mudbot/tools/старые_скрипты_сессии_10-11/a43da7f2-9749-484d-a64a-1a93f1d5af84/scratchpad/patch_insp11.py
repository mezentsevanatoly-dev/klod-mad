q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Прозрачный паучок плетёт паутину\\./, "
assert s.count(a) == 1
s = s.replace(a, a + "/кряж\\./, /проблемы\\./, ")
open(q, "wb").write(s.encode("cp1251"))
print("ok")
