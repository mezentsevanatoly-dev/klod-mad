import re, os
rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \|")
data = open(r"C:\Users\User\Desktop\Клод мад\mudbot\out.log", "rb").read()
# начало прогона: последний «Создан экземпляр зоны 'Тоннель бесов'»
key = "Создан экземпляр зоны 'Тоннель бесов'".encode("utf-8")
pos = data.rfind(key)
seg = data[pos:].decode("utf-8", errors="replace").splitlines()
cur, vis, kills = None, {}, {}
for l in seg:
    m = rx.match(l)
    if m and m.group(2).strip() == "Тоннель бесов":
        cur = m.group(1)
        vis[cur] = m.group(3).strip()
    elif "R.I.P." in l and cur:
        kills.setdefault(cur, []).append(l.split(" мертв")[0])
side = {"160068": "Трапезная", "160069": "Клетки", "160070": "Стойло", "160071": "Зал с куполом", "160072": "Разделочная",
        "160073": "Каменный мешок", "160074": "Котёл бесов", "160075": "Жаровни", "160076": "Молельня", "160082": "Алтарь",
        "160083": "Пещера ведьмы", "160058": "Портал бездны", "160059": "Обманный зал", "160061": "Зал обучения"}
for v, n in side.items():
    print(v, n, "посещена" if v in vis else "НЕ посещена", kills.get(v, ""))
print("всего клеток", len(vis))
