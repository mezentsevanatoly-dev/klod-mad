q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/кряж\\./, /проблемы\\./, "
assert s.count(a) == 1
s = s.replace(a, a + "/Громилы/, /Заколоченное окно/, /Камин/, /Карточные игры/, /Кости/, /Местный авторитет/, /Рулетка/, /^Угол$/, ")
open(q, "wb").write(s.encode("cp1251"))
t = open(r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js", "rb").read().decode("cp1251")
if '"притон"' not in t:
    t = t.replace('"канал": "Канализация"}', '"канал": "Канализация", "притон": "Притон"}')
    open(r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js", "wb").write(t.encode("cp1251"))
print("ok")
