# -*- coding: utf-8 -*-
"""Исправляет колонку «Описание в комнате» в areas/<зона>_mob.csv Айлины по строкам комнат из её claude_game.log:
бот узнаёт моба по строке комнаты, а в csv было скопировано чужое описание (все кобольды = «Молодой кобольд задумчиво разглядывает вас.»).
python tools/fix_desc_from_log.py <зона> [--apply]   (бэкап .bak_desc)"""
import os, re, sys, csv, io, shutil, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
J = os.path.join(BASE, "JMC БОТ АЙЛИНА")
zone = sys.argv[1]; apply = "--apply" in sys.argv
p = os.path.join(J, "areas", zone + "_mob.csv")
rows = list(csv.reader(open(p, "rb").read().decode("cp1251").splitlines(), delimiter=";", quotechar='"'))
hdr, body = rows[0], rows[1:]
logs = [os.path.join(J, "claude_game.log")] + sorted([os.path.join(J, "Logs", f) for f in os.listdir(os.path.join(J, "Logs"))] if os.path.isdir(os.path.join(J, "Logs")) else [])[-3:]
for a in sys.argv:
    if a.startswith("--log="):
        logs.append(a[6:])
cnt = collections.Counter()
BAD = re.compile(r"R\.I\.P|попытал|промах|ужалил|ударил|пришел|пришла|ушел|ушла|улетел|убежал|вошел|вошла|прилетел|исчез|появил|сказал|Вы |Кто-то|оглушен|состоянии|умирает|произнес|прибежал|прибежала|магические|ранен|мертв|ослеплен|\.\.\.")
for lp in logs:
    try:
        for s in open(lp, "rb").read().decode("cp1251", "replace").splitlines():
            m = re.match(r"^\d\d:\d\d:\d\d (.+)$", s)
            t = (m.group(1) if m else s).strip()
            if 12 < len(t) < 140 and t.endswith((".", "!")) and "H " not in t and not BAD.search(t):
                cnt[t] += 1
    except OSError:
        pass
changed = 0
for r in body:
    name = r[0].strip()
    if not name or len(r) < 2:
        continue
    cands = [(c, t) for t, c in cnt.items() if t.lower().startswith(name.lower()) and len(t) > len(name) + 4]
    cur = r[1].strip()
    if cur and any(t == cur for _, t in cands):
        continue
    if cands:
        cands.sort(reverse=True)
        new = cands[0][1] + " "
        print("%-22s | было: %-55s | стало: %s" % (name, cur[:55], new))
        r[1] = new; changed += 1
    elif cur:
        print("%-22s | В ЛОГЕ НЕТ строки; в csv: %s" % (name, cur[:60]))
print("исправлено:", changed)
if apply and changed:
    shutil.copy(p, p + ".bak_desc")
    s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows([hdr] + body)
    open(p, "wb").write(s.getvalue().encode("cp1251", "replace"))
    print("записано", p)
