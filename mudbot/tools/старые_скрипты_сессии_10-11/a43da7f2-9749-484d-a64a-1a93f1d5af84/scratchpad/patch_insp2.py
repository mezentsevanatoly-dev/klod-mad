p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
add = [w for w in ["/мышей\\./", "/хлипко\\./"] if w not in s]
a = "/оружием\\./, "
assert s.count(a) == 1
s = s.replace(a, a + ", ".join(add) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print(add)
