p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/Тупичок/, "
assert s.count(a) == 1
new = ["/сухих и завядших колючек или веток\\./", "/У сосны/", "/там, загляните вовнутрь\\./", "/обманут\\./"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
