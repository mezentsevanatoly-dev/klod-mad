"""Анализ опыта по логам пользователя (таблица exp_obs из tools/exp_from_logs.py) + мои замеры (mob_kills):
cap(L) — типичный максимум опыта за моба на лвл L (медиана при ур.моба >= L-2); доля cap за отставание моба; по каждому этапу (логу) — какая доля
убийств даёт полный опыт на лвл L и лучшее окно захода. python -X utf8 tools/exp_plan.py -> data/exp_plan.md
Рекомендуемое окно: верхний лвл H = максимальный L, при котором >= 70% убийств этапа дают полный опыт (моб >= L-2); окно (H-1 .. H).
"""
import os
import re
import sqlite3
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "game.db")


def main():
    db = sqlite3.connect(DB)
    lvl_of = {}
    for n, lv in db.execute("select name, level from mob_cards where level is not null and level != ''"):
        if str(lv).isdigit():
            lvl_of.setdefault(n.lower(), int(lv))
    for n, lv in db.execute("select name, mob_level from mob_kills where mob_level != '' and mob_level is not null"):
        if str(lv).isdigit():
            lvl_of.setdefault(n.lower(), int(lv))
    obs = []                                           # (лог, мой лвл, ур.моба, имя, опыт)
    for log, L, mob, e in db.execute("select log,my_level,mob,exp from exp_obs where exp>0"):
        m = lvl_of.get(mob.lower())
        if m:
            obs.append((log, L, m, mob, e))
    for n, ml, L, e in db.execute("select name, mob_level, my_level, exp from mob_kills where exp>0 and my_level>=21"):
        m = int(ml) if str(ml).isdigit() else lvl_of.get(n.lower())
        if m:
            obs.append(("замеры Айлины", L, m, n, e))
    byL = defaultdict(list)
    for _, L, m, _, e in obs:
        if L - m <= 2:
            byL[L].append(e)
    cap = {L: statistics.median(v) for L, v in byL.items() if len(v) >= 3}
    out = ["# Опыт за мобов: cap(лвл) и окна захода по этапам", "", "## cap(L) — типичный максимум за моба (медиана, моб >= L-2)", "",
           "| лвл | cap | замеров | cap/cap(L-1) |", "|---|---|---|---|"]
    prev = None
    for L in sorted(cap):
        out.append(f"| {L} | {int(cap[L])} | {len(byL[L])} | {'' if not prev else round(cap[L] / prev, 2)} |")
        prev = cap[L]
    ratio = defaultdict(list)
    for _, L, m, _, e in obs:
        if L in cap and L - m >= 3:
            ratio[L - m].append(e / cap[L])
    out += ["", "## Доля cap за отставание моба (мой лвл - лвл моба)", "", "| разница | доля (медиана) | замеров |", "|---|---|---|"]
    for d in sorted(ratio):
        if d <= 10:
            out.append(f"| {d} | {statistics.median(ratio[d]):.2f} | {len(ratio[d])} |")
    # этапы
    stages = defaultdict(list)
    for log, L, m, mob, e in obs:
        if log != "замеры Айлины":
            stages[log].append((L, m, mob, e))
    out += ["", "## Этапы пользователя: на каком лвл мобы дают полный опыт", "",
            "| этап | лвл в логе | мобов (убийств) | ур.мобов мин-мед-макс | доля полного опыта на L: | рекомендуемое окно |", "|---|---|---|---|---|---|"]
    rec = {}
    for log, rows in sorted(stages.items(), key=lambda kv: min(r[0] for r in kv[1])):
        ms = [r[1] for r in rows]
        if len(ms) < 8:
            continue
        shares = {}
        for L in range(max(1, min(ms) - 1), max(ms) + 4):
            shares[L] = sum(1 for m in ms if L - m <= 2 and m <= L + 3) / len(ms)
        ok = [L for L, s in shares.items() if s >= 0.7]
        H = max(ok) if ok else min(ms) + 2
        lvls = sorted({r[0] for r in rows})
        rec[log] = (H - 1, H)
        out.append(f"| {log} | {lvls[0]}-{lvls[-1]} | {len(ms)} | {min(ms)}-{int(statistics.median(ms))}-{max(ms)} | "
                   f"{' '.join(f'{L}:{int(s * 100)}%' for L, s in shares.items() if 0.3 <= s)} | {H - 1}-{H} |")
    out.append("\nМодель: лучше всего бить, когда ур.моба >= (мой лвл - 2) — тогда опыт = cap(лвл). Раньше (ниже) — безопасность и риск; позже — доля падает до 0.4 за 4 уровня разницы. "
               "cap растёт примерно в 1.7 раза за уровень, поэтому зону выгодно проходить на верхней границе окна.")
    open(os.path.join(ROOT, "data", "exp_plan.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
