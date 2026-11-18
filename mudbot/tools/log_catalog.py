# -*- coding: utf-8 -*-
"""Каталог по ЛОГАМ ПОЛЬЗОВАТЕЛЯ (Клод мад\\JMC\\*) и жаб: все убитые мобы по зонам (+опыт), все команды пользователя, заклинания игрока, названия зон.
Результат: mudbot/data/recon/ВСЕ_ЛОГИ/каталог_{мобы,команды,заклинания_игрока,зоны}.csv + каталог.md. Только чтение."""
import os, re, glob, collections, csv
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "recon", "ВСЕ_ЛОГИ"); os.makedirs(OUT, exist_ok=True)
ANSI = re.compile(r"\x1b\[[0-9;]*m|\[\d+(?:;\d+)*m")
skip = {".exe", ".dll", ".rar", ".ini", ".set", ".bat", ".dat", ".txt", ".png", ".webp"}
user_logs = [p for p in glob.glob(os.path.join(BASE, "JMC", "*")) if os.path.isfile(p) and os.path.splitext(p)[1].lower() not in skip and os.path.getsize(p) > 2000]
jaba = sorted(set(glob.glob(os.path.join(BASE, "JMC БОТ ИНКА", "Logs", "game_*.log")) + glob.glob(os.path.join(BASE, "JMC БОТ АЙЛИНА", "Logs", "game_*.log"))))
print("логов пользователя:", len(user_logs), "логов жаб:", len(jaba), flush=True)


def read(p):
    b = open(p, "rb").read()
    try:
        t = b.decode("utf-8")
        if "�" in t[:100000]:
            raise ValueError
    except Exception:
        t = b.decode("cp1251", "replace")
    return [ANSI.sub("", x).rstrip() for x in t.splitlines()]


RIP = re.compile(r"^(.+?) (?:мертв|мертва|мертво|мертвы)\. R\.I\.P\.")
EXP = re.compile(r"Вы получили (\d+) (?:единиц|единицу|единицы) опыта")
SP = re.compile(r"^Вы произнесли магические слова '([^']+)'")
ZN = re.compile(r"\[Зона[^:]*: ([^,\]]+?)(?:, ур\. ?([\d-]+))?\]")
ZN2 = re.compile(r"Создан экземпляр зоны '([^']+)'")
CMD = re.compile(r"^[а-яё!#.][^\.\!\?:]{0,38}$")
NOTCMD = re.compile(r"^(и|в|на|с|по|от|к|у|за|из|под|над|при|но|а|то|не|ни|же|ли|бы|вот|тут|там|вы |вас |вам |вам$)")
mob = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))   # zone -> name -> [kills, exp_sum]
cmds = collections.Counter(); cmd_zone = collections.defaultdict(collections.Counter); spells = collections.Counter(); zones = collections.Counter()
for p in user_logs:
    zone = os.path.basename(p)
    L = read(p)
    for i, s in enumerate(L):
        s = re.sub(r"^\[\d\d:\d\d:\d\d\] ?", "", s).strip()
        m = RIP.match(s)
        if m:
            e = 0
            for t in L[i + 1:i + 6]:
                me = EXP.search(t)
                if me:
                    e = int(me.group(1)); break
            nm = m.group(1).strip(); mob[zone][nm][0] += 1; mob[zone][nm][1] += e
            continue
        m = SP.match(s)
        if m:
            spells[m.group(1)] += 1; continue
        for z in ZN.finditer(s):
            zones[(z.group(1).strip(), z.group(2) or "")] += 1
        z2 = ZN2.search(s)
        if z2:
            zones[(z2.group(1), "область")] += 1
        if CMD.match(s) and not NOTCMD.match(s) and not re.search(r"\d+H \d+M", s) and len(s.split()) <= 5:
            cmds[s] += 1; cmd_zone[s][zone] += 1
for p in jaba:
    for s in read(p):
        s = re.sub(r"^\d\d:\d\d:\d\d ", "", s)
        if s.startswith(">> "):
            c = s[3:].strip()
            if c and not c.startswith("##") and len(c) < 80:
                cmds[c] += 1
with open(os.path.join(OUT, "каталог_мобы.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["зона-лог", "моб", "убито", "опыт_сумма", "опыт_средний"])
    for z in sorted(mob):
        for n, (k, e) in sorted(mob[z].items(), key=lambda x: -x[1][0]):
            w.writerow([z, n, k, e, e // k if k else 0])
with open(os.path.join(OUT, "каталог_команды.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["команда", "раз", "где чаще всего"])
    for c, n in cmds.most_common():
        w.writerow([c, n, "; ".join("%s×%d" % kv for kv in cmd_zone[c].most_common(3))])
with open(os.path.join(OUT, "каталог_заклинания_игрока.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["заклинание", "раз"])
    for c, n in spells.most_common():
        w.writerow([c, n])
with open(os.path.join(OUT, "каталог_зоны.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["зона", "уровни", "раз встретилась"])
    for (z, lv), n in sorted(zones.items(), key=lambda x: -x[1]):
        w.writerow([z, lv, n])
total_kills = sum(k for z in mob.values() for k, e in z.values())
names = set(n for z in mob.values() for n in z)
with open(os.path.join(OUT, "каталог.md"), "w", encoding="utf-8") as f:
    f.write("# Каталог по логам пользователя\nлогов: %d; убито всего: %d; разных мобов: %d; разных команд: %d; заклинаний игрока: %d; зон: %d\n\n" % (len(user_logs), total_kills, len(names), len(cmds), len(spells), len(set(z for z, _ in zones))))
    f.write("## Убито по логам (зона-лог: убийств / разных мобов)\n")
    for z in sorted(mob, key=lambda x: -sum(k for k, e in mob[x].values())):
        f.write("- %s: %d / %d\n" % (z, sum(k for k, e in mob[z].values()), len(mob[z])))
    f.write("\n## 60 самых частых команд пользователя\n")
    for c, n in cmds.most_common(60):
        f.write("- `%s` ×%d\n" % (c, n))
    f.write("\n## Заклинания игрока\n")
    for c, n in spells.most_common(40):
        f.write("- %s ×%d\n" % (c, n))
print("ГОТОВО: убито", total_kills, "мобов", len(names), "команд", len(cmds), "заклинаний", len(spells), "зон", len(set(z for z, _ in zones)), flush=True)
