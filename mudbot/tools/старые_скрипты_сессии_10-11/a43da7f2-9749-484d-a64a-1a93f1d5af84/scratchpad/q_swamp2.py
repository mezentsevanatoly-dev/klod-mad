import re
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\болото_часть", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
print(len(log))
shown = 0
for i, l in enumerate(log):
    s = l.strip()
    if not s or s.startswith(("+", "|", ":")) or re.match(r"^\d+H \d+M", s):
        continue
    if re.search(r"Зона|область|обл |Создан экземпляр|Вы сможете|Добро|Болото", s) or s in ("север", "юг", "восток", "запад", "вверх", "вниз"):
        print(i, s[:100]); shown += 1
    if shown > 45: break
