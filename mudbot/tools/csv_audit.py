# -*- coding: utf-8 -*-
"""Проверка списков мобов зон Айлины: бот узнаёт моба по «Описанию в комнате», поэтому плохо, если
 - у разных мобов одинаковое описание (скопировано одно на всех),
 - описание похоже на строку боя/квеста/движения, а не на строку моба в комнате,
 - описание пустое.
Дополнительно: есть ли такая строка в логах (бота Айлины и логах пользователя JMC\\*) - если нет ни разу, бот её не увидит.
python tools/csv_audit.py [зона ...]"""
import os, re, io, sys, csv, glob, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
A = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
BAD = re.compile(r"R\.I\.P|попытал|промах|ударил|рубанул|мертв|оглушен|произнес|прибежал|прилетел|пришел|пришла|ушел|ушла|убежал|улетел|выполнено|Вы |состоянии|ранен|умирает|сказал|исчез|встал|выбыл")
zones = sys.argv[1:] or ["бесы", "храм", "геоканал3", "рр2_СтараяЦерковь", "24плюс", "кочи", "рыбка", "луга", "конюшни"]
# все строки логов (одним множеством)
seen = set()
for p in [os.path.join(BASE, "JMC БОТ АЙЛИНА", "claude_game.log"), os.path.join(BASE, "JMC БОТ ИНКА", "claude_game.log")] + glob.glob(os.path.join(BASE, "JMC", "*")):
    if os.path.isfile(p) and os.path.getsize(p) < 60_000_000:
        for s in open(p, "rb").read().decode("cp1251", "replace").splitlines():
            t = re.sub(r"^\[?\d\d:\d\d:\d\d\]? ", "", s).strip()
            if 10 < len(t) < 200:
                seen.add(t)
for z in zones:
    p = os.path.join(A, z + "_mob.csv")
    if not os.path.exists(p):
        print("==", z, "нет csv"); continue
    rows = [r for r in csv.reader(open(p, "rb").read().decode("cp1251", "replace").splitlines(), delimiter=";", quotechar='"')][1:]
    rows = [r for r in rows if r and r[0].strip()]
    by = collections.defaultdict(list)
    for r in rows:
        by[r[1].strip()].append(r[0].strip())
    dup = {d: n for d, n in by.items() if len(set(n)) > 1}
    bad = [(r[0], r[1].strip()) for r in rows if BAD.search(r[1])]
    empty = [r[0] for r in rows if not r[1].strip()]
    unseen = [(r[0], r[1].strip()) for r in rows if r[1].strip() and r[1].strip() not in seen and r[1].split("...")[0].strip() not in seen]
    print("== %s: мобов %d | одно описание на разных: %d | похоже на бой/движение: %d | пусто: %d | ни разу нет в логах: %d" % (z, len(rows), sum(len(v) for v in dup.values()), len(bad), len(empty), len(unseen)))
    for d, n in dup.items():
        print("   ОДНО НА ВСЕХ:", d[:60], "->", ", ".join(sorted(set(n))))
    for n, d in bad:
        print("   БОЙ/ДВИЖЕНИЕ:", n, "|", d[:70])
    for n, d in unseen[:12]:
        print("   НЕТ В ЛОГАХ:", n, "|", d[:70])
