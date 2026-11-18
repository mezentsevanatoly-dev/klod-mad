# -*- coding: utf-8 -*-
"""Пересчёт «строка в комнате -> имя моба» в explore.json: эксплорер считал строкой моба и подсказки зон «[Зона, на север: ...]»,
из-за этого в пограничных клетках пары сдвигались. Здесь строки на «[» отбрасываются, пары берутся по порядку (смотреть N.).
Запуск: python -X utf8 tools/luga_fix_lines.py"""
import os, re, json, collections

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(BASE, "mudbot", "data", "recon", "луга_айлина", "explore.json")
S = json.load(open(P, encoding="utf-8"))


def short(l):
    return re.sub(r"\s*\.\.\..*$", "", l).strip() + " "


cnt = collections.defaultdict(collections.Counter)
bad_cells = 0
for vn, c in S["cells"].items():
    ents = [l for l in c.get("mobs_lines", []) if not l.startswith("[")]
    names = c.get("mobs", [])
    if len(ents) != len(names):
        bad_cells += 1
        continue
    for l, n in zip(ents, names):
        cnt[short(l)][n] += 1
def stem_hit(name, line):
    ws = [w[:5].lower() for w in re.findall(r"[А-Яа-яЁё]+", name) if len(w) > 3]
    return sum(1 for w in ws if w in line.lower())


main = {}
for l, c in cnt.items():
    cand = [n for n in c]
    if len(cand) > 1:                                   # общая строка: берём вид, слова которого есть в самой строке
        sc = sorted(((stem_hit(n, l), n) for n in cand), reverse=True)
        if sc[0][0] > 0 and (len(sc) == 1 or sc[0][0] > sc[1][0]):
            main[l] = sc[0][1]; continue
    main[l] = c.most_common(1)[0][0]
# клетки, где число строк и имён не сошлось: вычитаем уже известные пары, остаток 1 к 1
for vn, c in S["cells"].items():
    ents = [short(l) for l in c.get("mobs_lines", []) if not l.startswith("[")]
    names = list(c.get("mobs", []))
    if len(ents) == len(names):
        continue
    ents2, names2 = list(ents), list(names)
    for l in list(ents2):
        n = main.get(l)
        if n in names2:
            names2.remove(n); ents2.remove(l)
    if len(ents2) == 1 and len(names2) == 1 and ents2[0] not in main:
        main[ents2[0]] = names2[0]
# виды без строки: ищем строку в клетках по словам имени (не менее 2 слов-основ), если она одна и ещё не занята
allines = set()
for vn, c in S["cells"].items():
    for l in c.get("mobs_lines", []):
        if not l.startswith("["):
            allines.add(short(l))
for nm in S["cards"]:
    if nm in set(main.values()):
        continue
    cand = [l for l in allines if l not in main and stem_hit(nm, l) >= 2]
    if len(cand) == 1:
        main[cand[0]] = nm
S["line2name"] = main
S["line_conflicts"] = {l: sorted(c) for l, c in cnt.items() if len(c) > 1 and not any(stem_hit(n, l) for n in c)}
json.dump(S, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
names = set(S["line2name"].values())
print("клеток с несовпадением число строк/имён (пропущены):", bad_cells)
print("строк в комнате -> имя:", len(S["line2name"]), "| видов без строки:", [n for n in S["cards"] if n not in names])
print("общие строки у разных видов:", S["line_conflicts"] or "нет")


