p = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
s = open(p, "rb").read().decode("cp1251")
import shutil
shutil.copyfile(p, p + ".bak_nowait")
a = 'var AREA_NAMES = '
assert s.count(a) == 1
s = s.replace(a, 'var AREA_NOWAIT = {"притон": 1};   // zones where a cooldown is NOT waited for: walk into the existing area / the zone at once\r\n' + a)
b = "\t\tif (this.areaCool > 0) {\r\n\t\t\tthis.BotInZone = false;"
assert s.count(b) == 1, s.count(b)
s = s.replace(b, "\t\tif (this.areaCool > 0 && typeof AREA_NOWAIT != \"undefined\" && AREA_NOWAIT[zonename]) {\r\n"
    "\t\t\tthis.areaPhase = null;\r\n\t\t\tthis.BotInZone = true;\r\n"
    "\t\t\tthis.areaNote(\"AREA_NOWAIT zone=\" + this.areaCoolName + \" cooldown=\" + this.areaCool + \" -> walking in\");\r\n"
    "\t\t\tthis.wait(10);\r\n\t\t\treturn;\r\n\t\t}\r\n" + b)
open(p, "wb").write(s.encode("cp1251"))
print("ok")
