p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/мышей\\./, /хлипко\\./, "
assert s.count(a) == 1
s = s.replace(a, a + "/пришла в норму/, ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
