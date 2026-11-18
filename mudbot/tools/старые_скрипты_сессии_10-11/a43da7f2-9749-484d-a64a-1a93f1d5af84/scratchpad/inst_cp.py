import shutil
sp = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\CardProbe.js"
T = r"C:\Users\User\Desktop\Тадия"
src = open(sp, encoding="utf-8").read().replace("\r\n", "\n").replace("\n", "\r\n")
open(T + r"\scripts\CardProbe.js", "wb").write(src.encode("cp1251"))
p = T + r"\settings\дкаре.js"
shutil.copyfile(p, p + ".bak_cp")
s = open(p, "rb").read().decode("cp1251")
a = 'include("scripts/AreaGuard.js");'
assert s.count(a) == 1
if "CardProbe" not in s:
    s = s.replace(a, a + '\r\ninclude("scripts/CardProbe.js");     // карточка моба без уровня: смотреть перед боем')
open(p, "wb").write(s.encode("cp1251"))
print("ok")
