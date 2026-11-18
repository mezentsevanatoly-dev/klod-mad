import re
p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\barb_levelup.py"
t = open(p, encoding="utf-8").read()
zones = {"park": "Парк", "alleya": "Аллея", "kanal": "Канализация", "pritn": "Притон", "sklad1": "Склад в Геоланте",
         "privy1": "Дом с привидениями", "sklad2": "Склад в Геоланте", "privy2": "Дом с привидениями"}
for key, z in zones.items():
    t = re.sub(r'if create\("([^"]+)"\):(\s+mapfight\("' + key + '")', lambda m: f'if create("{m.group(1)}", "{z}"):{m.group(2)}', t)
# катакомбы (hatch после create)
t = re.sub(r'if create\("вни"\):(\s+hatch\(\))', r'if create("вни", "Катакомбы Геоланта"):\1', t)
open(p, "w", encoding="utf-8").write(t)
print([l.strip() for l in t.splitlines() if "if create(" in l])
