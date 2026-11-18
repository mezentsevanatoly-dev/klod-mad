p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/Родник/, "
assert s.count(a) == 1
new = ["/когда-нибудь будут починены\\./", "/скалами\\./", "/Белая мышка притаилась в углу\\./", "/сухой соломы\\./", "/стороне\\./", "/поросли оказывают гнетущее впечатление\\./"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
