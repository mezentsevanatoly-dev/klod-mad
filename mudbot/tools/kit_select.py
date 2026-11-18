"""Выбор комплектов варвара из КСК (ksk_items) и биржи (ex_items + exch_lots) по приоритетам пользователя:
АС с потенциалом звёзд (+2 за каждое улучшение: 1 звезда -> 1, 3 -> 2, 6 -> 3), броня, таймер, цена; одна вещь на слот, общих вещей в комплектах нет.
python -X utf8 tools/kit_select.py [--json путь]      печатает три комплекта: сет1 (мин.ур <= 8), сет2 (9-12), сет3 (13-20)
Уникальные вещи (синие) помечены «У»: их скрытые свойства видны только в `х`.
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "game.db")
SLOT_N = {"доп": 1, "голова": 1, "шея": 2, "тело": 1, "плечи": 1, "талия": 1, "кисти": 1, "руки": 1, "ноги": 1, "обувь": 1, "запястье": 2, "палец": 2}
PH = {"на голову": "голова", "на шею": "шея", "на тело": "тело", "вокруг талии": "талия", "на кисти рук": "кисти", "на руки": "руки",
      "на ноги": "ноги", "как обувь": "обувь", "на запястье": "запястье", "на палец": "палец", "на дополнительный слот": "доп"}
QSLOT = {"доп": "доп", "голов": "голова", "шея": "шея", "тело": "тело", "плеч": "плечи", "талия": "талия", "кист": "кисти", "руки": "руки",
         "ноги": "ноги", "обув": "обувь", "запя": "запястье", "палец": "палец"}
BUCKETS = [(1, 0, 8, 40_000), (2, 9, 12, 120_000), (3, 13, 20, 400_000)]      # (комплект, мин.ур от, до, потолок цены вещи)
MIN_TIMER = {1: 8000, 2: 8000, 3: 8000}


def improvements(stars):
    k = 0
    while (k + 1) * (k + 2) // 2 <= stars:
        k += 1
    return k


def slot_of(phrase, hint=""):
    for k, v in PH.items():
        if k in phrase:
            return v
    return hint or "плечи"


def load():
    db = sqlite3.connect(DB)
    cands = []
    for dept, name, slot, minlvl, ac, cut, crush, pierce, stars, timer, uni, special, cnt, rating, flags in db.execute(
            "select dept,name,slot,minlvl,ac,cut,crush,pierce,stars,timer,unique_flag,special,cnt,rating,flags from ksk_items"):
        sl = slot_of(slot)
        if "!РЕНТ" in (flags or ""):
            continue
        for i in range(max(1, cnt)):                              # N одинаковых предметов в отделе = N кандидатов
            cands.append(dict(src=f"КСК:{dept}", ref=f"{name}#{i}", name=name, slot=sl, minlvl=minlvl, ac=ac, arm=(cut + crush + pierce) / 3,
                              stars=stars, timer=timer, uni=uni, price=0, cnt=cnt, rating=rating.split(",")[1] if "," in rating else ""))
    lots = {}
    for lot, name, price, timer, rt, slot, lvl in db.execute("select lot,name,price,timer,rating,slot,lvl from exch_lots"):
        lots.setdefault(name, []).append((price, lot, timer, slot))
    for name, title, slot, minlvl, ac, cut, crush, pierce, stars, timer, uni, rating, flags in db.execute(
            "select name,title,slot,minlvl,ac,cut,crush,pierce,stars,timer,unique_flag,rating,flags from ex_items"):
        if "!РЕНТ" in (flags or ""):
            continue
        for price, lot, ltimer, qslot in sorted(lots.get(name, [])):
            cands.append(dict(src="биржа", ref=lot, name=name, slot=slot_of(slot, QSLOT.get(qslot, "плечи")), minlvl=minlvl, ac=ac,
                              arm=(cut + crush + pierce) / 3, stars=stars, timer=ltimer, uni=uni, price=price, cnt=1,
                              rating=rating.split(",")[1] if "," in rating else ""))
    return cands


def score(c):
    return (c["ac"] + 2 * improvements(c["stars"])) * 10 + c["arm"] * 2 + min(c["timer"], 40000) / 4000 - c["price"] / 100000 + c.get("bonus", 0)


def main():
    cands = load()
    if "--ksk-only" in sys.argv:                     # сначала собираем комплекты только из того, что есть на КСК; биржа — потом, в поисках лучшего
        cands = [c for c in cands if c["src"].startswith("КСК")]
    used_names, sets = set(), {}
    for sid, lo, hi, cap in BUCKETS:
        chosen = {}
        for c in cands:                                 # вещи, уже лежащие в этом комплекте, не двигаем (бонус); лежащие в чужом :следак — недоступны
            c["bonus"] = 6 if c["src"] == f"КСК:Следак{sid}" else 0
        for slot, n in SLOT_N.items():
            pool = [c for c in cands if c["slot"] == slot and c["minlvl"] <= hi and c["price"] <= cap and c["timer"] >= MIN_TIMER[sid]
                    and (c["src"], c["ref"]) not in used_names
                    and not (c["src"].startswith("КСК:Следак") and c["src"] != f"КСК:Следак{sid}")]
            inb = [c for c in pool if lo <= c["minlvl"] <= hi]
            ranked = sorted(inb, key=score, reverse=True) + sorted([c for c in pool if c not in inb], key=score, reverse=True)
            picks, names = [], {}
            for c in ranked:
                if len(picks) >= n:
                    break
                if any(p["src"] == c["src"] and p["ref"] == c["ref"] for p in picks):
                    continue
                picks.append(c)
            for p in picks:
                used_names.add((p["src"], p["ref"]))
            chosen[slot] = picks
        sets[sid] = chosen
    total = {}
    for sid, ch in sets.items():
        print(f"\n=== комплект {sid} (мин.ур {dict((b[0], b[1:3]) for b in BUCKETS)[sid]})")
        cost = 0
        for slot, picks in ch.items():
            if not picks:
                print(f"  {slot:9} — нет кандидатов")
            for p in picks:
                cost += p["price"]
                print(f"  {slot:9} {p['name']:36} мин{p['minlvl']:>3} АС{p['ac']:>3}+{2 * improvements(p['stars'])} ар{p['arm']:.0f} зв{p['stars']} т{p['timer']:>6} "
                      f"{'У' if p['uni'] else ' '} {p['src']}:{p['ref']} {p['price'] or ''}")
        total[sid] = cost
        print("  купить на:", cost)
    if "--json" in sys.argv:
        json.dump({str(k): {s: [dict(p) for p in v] for s, v in ch.items()} for k, ch in sets.items()},
                  open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
