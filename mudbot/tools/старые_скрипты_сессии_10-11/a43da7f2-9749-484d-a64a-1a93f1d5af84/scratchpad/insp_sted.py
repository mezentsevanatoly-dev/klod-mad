q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/^арка\\.$/, /Здешние кареты отличаются особенным удобством в езде\\./, /не хотите потерять свой кошелек\\./, /свежей трухи\\./, /мрамором\\./, ")
open(q, "wb").write(s.encode("cp1251"))
print("ok")
