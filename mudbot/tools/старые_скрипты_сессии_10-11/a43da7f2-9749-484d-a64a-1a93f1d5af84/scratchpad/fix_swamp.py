p = r"C:\Users\User\Desktop\Тадия\areas\болото.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
last_v = max(i for i, l in enumerate(L) if l.startswith("#if"))
L.insert(last_v + 1, ".триг #scr botCore.BotInZone = false")
open(p, "wb").write("\r\n".join(L).encode("cp1251"))
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Головоногий моллюск приклеился ко дну\\./, "
assert s.count(a) == 1
s = s.replace(a, a + "/Утиное гнездо/, /Прозрачный паучок плетёт паутину\\./, ")
open(q, "wb").write(s.encode("cp1251"))
print("ok", len(L))
