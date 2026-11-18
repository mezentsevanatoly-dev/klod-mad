p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/пришла в норму/, "
assert s.count(a) == 1
new = ["/Банк/", "/проясняет ситуацию\\./", "/можно было сшить сапоги, скроить одежду, починить оружие и многое другое\\./", "/Продавец:/"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
