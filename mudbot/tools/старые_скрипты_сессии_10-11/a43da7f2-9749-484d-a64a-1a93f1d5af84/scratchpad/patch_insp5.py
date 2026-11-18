p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/Продавец:/, "
assert s.count(a) == 1
new = ["/посетителями\\./", "/развесистый куст\\./", "/куст\\./", "/Дупло/", "/Тупичок/"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
