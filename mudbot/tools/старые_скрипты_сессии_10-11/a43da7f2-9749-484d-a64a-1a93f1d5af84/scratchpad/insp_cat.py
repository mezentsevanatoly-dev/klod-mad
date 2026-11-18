q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/Освещенный пятачок/, /Святилище кобольдов/, ")
open(q, "wb").write(s.encode("cp1251"))
g = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t = open(g, "rb").read().decode("cp1251")
if '"каты1"' not in t:
    t = t.replace('"леч": "Лечебница для животных"}', '"леч": "Лечебница для животных", "каты1": "Катакомбы Геоланта"}').replace('"леч": 1}', '"леч": 1, "каты1": 1}')
    open(g, "wb").write(t.encode("cp1251"))
print("ok")
