"""Итоги эксплора по всем зонам -> ЗОНЫ\\ИТОГИ.md: клеток пройдено / в маппере, переходы, закрытые выходы, мобов."""
import os, json, glob
K = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Z = os.path.join(K, "ЗОНЫ")
out = ["# Итоги эксплора", "", "| Зона | Клеток | В маппере | Переходов | Закрытых выходов | Мобов |", "|---|---|---|---|---|---|"]
details = []
for d in sorted(glob.glob(os.path.join(Z, "*", "клетки.csv"))):
    zone = os.path.basename(os.path.dirname(d))
    R = [l.split(";") for l in open(d, encoding="cp1251").read().splitlines()[1:]]
    tr = open(os.path.join(os.path.dirname(d), "переходы.csv"), encoding="cp1251").read().splitlines()[1:]
    closed = [(r[0], r[1], c) for r in R for c in (r[3].split(",") if len(r) > 3 and r[3] else []) if "другая зона" not in c]
    w = os.path.join(K, "mudbot", "data", "world", zone + ".json")
    mp = len(json.load(open(w, encoding="utf-8"))["rooms"]) if os.path.exists(w) else "—"
    mf = os.path.join(K, "JMC БОТ АЙЛИНА", "areas", "эксплор_" + zone.replace(" ", "_") + "_mob.csv")
    mobs = max(0, len(open(mf, encoding="cp1251", errors="replace").read().splitlines()) - 1) if os.path.exists(mf) else 0
    out.append("| %s | %d | %s | %d | %d | %d |" % (zone, len(R), mp, len(tr), len(closed), mobs))
    details += ["", "## " + zone, "", "Переходы:"] + ["- " + t for t in tr]
    if closed:
        details += ["", "Закрытые выходы:"] + ["- %s %s: %s" % c for c in closed]
open(os.path.join(Z, "ИТОГИ.md"), "w", encoding="utf-8").write("\n".join(out + details) + "\n")
print("\n".join(out))
