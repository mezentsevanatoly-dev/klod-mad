import shutil
sp = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\BotFix.js"
T = r"C:\Users\User\Desktop\Тадия"
src = open(sp, encoding="utf-8").read().replace("\r\n", "\n").replace("\n", "\r\n")
open(T + r"\scripts\BotFix.js", "wb").write(src.encode("cp1251"))
p = T + r"\settings\дкаре.js"
shutil.copyfile(p, p + ".bak_bf")
s = open(p, "rb").read().decode("cp1251")
a = 'include("scripts/ZoneLevel.js");'
assert s.count(a) == 1
if "BotFix" not in s:
    s = s.replace(a, a + '\r\ninclude("scripts/BotFix.js");       // шаг не повторять, если ход удался')
open(p, "wb").write(s.encode("cp1251"))
print("ok")
