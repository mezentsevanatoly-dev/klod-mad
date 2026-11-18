# -*- coding: utf-8 -*-
"""Четыре словаря мобов для бота (слова пользователя 12-13.11):
  убивать  - csv зон (areas/<зона>_mob.csv), здесь не дублируется;
  мирные   - mobs.flags [Мирный] из game.db + названные пользователем;
  квестовые- не бить до сдачи (вдова, отшельник ...);
  ассист   - data/ассист_мобы.csv (+ названные пользователем), для mkill и «клетку не бить».
Пишет mudbot/data/словари/{мирные,квестовые,ассист,не_бить_клетку}.csv и вставляет JS-регэкспы в scripts/BotCore.js Айлины между маркерами // DICTS-BEGIN и // DICTS-END."""
import os, re, csv, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "словари"); os.makedirs(OUT, exist_ok=True)
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
peace = {}
for (n, fl) in c.execute("select name,flags from mobs where flags like '%Мирный%'"):
    peace[n.strip()] = "mobs.flags " + fl
MAN_PEACE = {"торговец": "рыбка: мирный (слова пользователя)", "вдова": "рыбка: мирная (слова пользователя)", "смотритель парка": "парк: садовник/смотритель, мирный", "смотритель канализации": "канал: мирный (слова пользователя)",
             "кладовщик": "склад", "темнокожий носильщик": "порт: не бить (таможенник его лечит)", "старый таможенник": "порт: свита таможенника не бить", "дэрия": "порт: бордель", "лили": "порт: бордель",
             "учитель": "Мад школа: учитель на входе не бить"}
peace.update(MAN_PEACE)
quest = {"костяной дух": "рыбка: задание (из лога зада)", "разъяренный энт": "рыбка: задание (амулет вдове)", "отражение повелителя зеркала": "рыбка: задание Контара", "бездомный": "церковь: задание (из лога зада)", "кантор": "церковь: задание", "пыльное облако": "церковь: задание"}
assist = {}
for r in csv.reader(open(os.path.join(ROOT, "data", "ассист_мобы.csv"), encoding="utf-8-sig"), delimiter=";"):
    if r and r[0] != "моб-ассист" and len(r) > 1 and r[1].isdigit() and int(r[1]) >= 3:
        assist[r[0].strip()] = "логи: помог %s раз" % r[1]
for n, why in {"Управляющий складом": "склад: ассист, в клетке никого не бить", "Охранник склада": "склад: ассист", "Дюжий охранник": "рыбка: ассист", "Капитан эльфийского судна": "рыбка: ассист, первым", "Городской страж": "города: ассист", "Стражник": "города: ассист",
               "Начальник городской стражи": "Геолант: ассист", "Охранник банка": "Геолант: ассист", "Облако испарений": "Геолант: чумная группа, ассист", "Сеятель чумы": "Геолант: чумная группа", "Больной старик": "Геолант: чумная группа",
               "Зловонное порождение": "Геолант: чумная группа", "Зараженный лучник": "Геолант: чумная группа", "Беглец из лепрозория": "ассистит всем мобам, сам не агро"}.items():
    assist[n] = why
nokill_cell = ["Облако испарений", "Облако ядовитых испарений", "Сеятель чумы", "Зловонное порождение", "Жуткое порождение", "Больной старик", "Зараженный лучник", "Темный всадник", "Начальник городской стражи", "Охранник банка", "Охранники банка", "Управляющий складом"]
# слова пользователя 13.11: ассист-моб в клетке с целью из списка -> не бить (словарь ассист); цели (имена в csv зон) сюда не входят
import glob as _gl
_targets = set()
for _p in _gl.glob(os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas", "*_mob.csv")):
    try:
        for _r in csv.reader(open(_p, "rb").read().decode("cp1251").splitlines(), delimiter=";", quotechar='"'):
            if _r:
                _targets.add(_r[0].strip().lower())
    except Exception:
        pass
avoid_extra = [n for n in assist if n.lower() not in _targets and len(n) >= 5 and n not in nokill_cell and not n.endswith(("ь", "й")) or (n.lower() not in _targets and len(n) >= 5 and n not in nokill_cell)]
avoid_extra = []      # слова пользователя 13.11: обходим только названную группу (чума, начальник стражи, охрана банка, управляющий); остальные ассисты бьются по одному (kill, не mkill)
nokill_cell = nokill_cell + avoid_extra
for nm, d, hdr in (("мирные", peace, "имя;откуда"), ("квестовые", quest, "имя;откуда"), ("ассист", assist, "имя;откуда"), ("не_бить_клетку", {x: "" for x in nokill_cell}, "имя;откуда")):
    with open(os.path.join(OUT, nm + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(hdr + "\n")
        for k, v in sorted(d.items()):
            f.write("%s;%s\n" % (k, v))
    print(nm, len(d))
rx = lambda L: "|".join(re.escape(x).replace("\\ ", " ") for x in L if len(x) >= 4)
js = ["// DICTS-BEGIN (build_dicts.py, 13.11: словари мирных/квестовых/не_бить_клетку)",
      "var PEACE_MOBS = /%s/i;" % rx(sorted(peace)),
      "var QUEST_MOBS = /%s/i;" % rx(sorted(quest)),
      "var FIRST_MOBS = {\"Капитан эльфийского судна\": 1};",
      "var AVOID_MOBS = /%s/;" % rx(nokill_cell),
      "// DICTS-END"]
p = os.path.join(BASE, "JMC БОТ АЙЛИНА", "scripts", "BotCore.js")
enc = "cp1251"
t = open(p, "rb").read().decode(enc)
block = "\r\n".join(js)
if "// DICTS-BEGIN" in t:
    t = re.sub(r"// DICTS-BEGIN.*?// DICTS-END", lambda m: block, t, flags=re.S)
else:
    t = re.sub(r"var AVOID_MOBS = [^\r\n]*", lambda m: block, t, count=1)
    chk = "if (typeof AVOID_MOBS != \"undefined\" && AVOID_MOBS.test(mobLookName)) { this.skipRoom = true; }"
    add = chk + "\r\n\t\t\tif (typeof PEACE_MOBS != \"undefined\" && PEACE_MOBS.test(mobLookName)) { return sTextLine; }   // мирных и квестовых не целим"
    if "PEACE_MOBS.test" not in t:
        t = t.replace(chk, add, 1)
open(p, "wb").write(t.encode(enc, "replace"))
print("BotCore.js обновлён")
