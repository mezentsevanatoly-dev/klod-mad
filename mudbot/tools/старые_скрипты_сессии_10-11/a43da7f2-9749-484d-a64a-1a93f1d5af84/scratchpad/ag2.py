p = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
s = open(p, "rb").read().decode("cp1251")
a = '"конюшни": "Конюшни"}'
if '"каты2": "Катакомбы Геоланта"' not in s: s = s.replace(a, '"конюшни": "Конюшни", "каты2": "Катакомбы Геоланта"}', 1)
open(p, "wb").write(s.encode("cp1251"))
print('"каты2": "Катакомбы Геоланта"' in s)
