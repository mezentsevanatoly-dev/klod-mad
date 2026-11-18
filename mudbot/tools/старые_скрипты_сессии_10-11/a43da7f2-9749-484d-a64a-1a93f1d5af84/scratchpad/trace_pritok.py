import re
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\притон", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(log) if l.strip() == "область создать с" or l.strip().startswith("область создать с"))
M = {"север", "юг", "восток", "запад", "вверх", "вниз", "с", "ю", "в", "з"}
room, ex = "?", "?"
out = []
for i in range(i0, min(len(log), i0 + 2500)):
    l = log[i].rstrip()
    if l.startswith("[ Exits"):
        ex = l
        # название комнаты — ближайшая выше строка без отступа и без точки
        for k in range(i - 1, max(i0, i - 12), -1):
            s = log[k].strip()
            if s and not log[k].startswith(" ") and not s.endswith((".", "!", "?", ",")):
                room = s; break
        continue
    s = l.strip()
    if s in M or s.startswith("убить") or s.startswith("у "):
        out.append((s, room, ex.replace("[ Exits: ", "").replace(" ]", "")))
    m = re.match(r"^(Вы не можете идти|Не получится|Алкоголь|Закрыто|Дверь)", s)
    if m:
        out.append(("   !!" + s[:50], room, ex))
for a in out[:75]:
    print(a)

