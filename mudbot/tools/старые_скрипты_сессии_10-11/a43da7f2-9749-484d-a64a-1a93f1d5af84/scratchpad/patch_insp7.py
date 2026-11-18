p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/обманут\\./, "
assert s.count(a) == 1
new = ["/обул(ась|ся) в /", "/увеличилась в размерах/", "/создал[аи]? сгусток теней/"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
