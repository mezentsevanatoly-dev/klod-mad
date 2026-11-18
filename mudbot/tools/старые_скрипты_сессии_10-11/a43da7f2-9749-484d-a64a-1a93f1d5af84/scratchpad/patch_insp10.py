p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(p, "rb").read().decode("cp1251")
a = "/поросли оказывают гнетущее впечатление\\./, "
assert s.count(a) == 1
new = ["/Жидкая грязь/", "/Крысиное гнездо/", "/Решетка/", "/Фильтр/", "/Переулок Лихой/", "/Паучок плетет в углу свою паутинку\\./", "/Головоногий моллюск приклеился ко дну\\./"]
s = s.replace(a, a + ", ".join(new) + ", ")
open(p, "wb").write(s.encode("cp1251"))
q = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t = open(q, "rb").read().decode("cp1251")
if '"канал"' not in t:
    t = t.replace('"аллея": "Аллея"}', '"аллея": "Аллея", "канал": "Канализация"}')
    open(q, "wb").write(t.encode("cp1251"))
print("ok")
