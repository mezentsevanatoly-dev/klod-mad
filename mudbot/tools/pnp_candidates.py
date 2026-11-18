# -*- coding: utf-8 -*-
"""ПнП-кандидаты: строки логов жаб (Айлина и Кимпи), которые НЕ совпадают ни с одним регэкспом словаря InspectionWords (в shared\\Inspection.js),
то есть те, что окно «ПнП-с» показывало бы как неизвестные. Обычный текст игры (по словарю слов из логов) можно внести в словарь, строки,
похожие на настоящую проверку присутствия (бессмысленные слова), НЕ вносятся и не трогаются.
  python tools/pnp_candidates.py            -> отчёт (data/pnp/кандидаты.txt)
  python tools/pnp_candidates.py --apply    -> дописать понятные строки в shared\\Inspection.js (бэкап рядом)"""
import os, re, sys, glob, collections, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
SHARED = os.path.join(BASE, "shared", "Inspection.js")
OUT = os.path.join(ROOT, "data", "pnp"); os.makedirs(OUT, exist_ok=True)
LOGS = []
for j in ("JMC БОТ АЙЛИНА", "JMC БОТ ИНКА"):
    LOGS += [p for p in glob.glob(os.path.join(BASE, j, "Logs", "game_2026-11-1*.log")) if "до_" not in p]
    LOGS.append(os.path.join(BASE, j, "claude_game.log"))

src = open(SHARED, "rb").read().decode("cp1251")
body = src[src.index("var InspectionWords = [") + 23: src.rindex("];")]
TOK = re.compile(r"/((?:\\.|\[(?:\\.|[^\]])*\]|[^/\n\\])+)/([gimy]*)")
pats = []
for m in TOK.finditer(body):
    fl = 0
    if "i" in m.group(2): fl |= re.I
    try:
        pats.append(re.compile(m.group(1), fl))
    except re.error:
        pass
print("регэкспов в словаре:", len(pats))

SKIP = re.compile(r"^(>> |## |#|\d+H \d+M|.*Вых:|\[ Exits|\[Зона|\[Группа|\s*$)")


def matches(s):
    for p in pats:
        if p.search(s):
            return True
    return False


cnt = collections.Counter()
for path in LOGS:
    try:
        data = open(path, "rb").read().decode("cp1251", "replace").splitlines()
    except OSError:
        continue
    for s in data:
        s = re.sub(r"^\d\d:\d\d:\d\d ", "", s).rstrip()
        if SKIP.match(s) or len(s) < 6:
            continue
        if not matches(s):
            cnt[s] += 1
print("уникальных непопавших строк:", len(cnt))

# словарь слов из логов (для отделения обычного текста игры от бессмыслицы проверки)
voc = collections.Counter()
for path in LOGS:
    try:
        for w in re.findall(r"[а-яё]{3,}", open(path, "rb").read().decode("cp1251", "replace").lower()):
            voc[w] += 1
    except OSError:
        pass
known = {w for w, c in voc.items() if c >= 5}


def kind(s):
    ws = re.findall(r"[а-яё]{3,}", s.lower())
    if not ws:
        return "пропуск"
    unk = sum(1 for w in ws if w not in known) / len(ws)
    if re.match(r"^[А-ЯЁ][а-яё]+( [а-яё]+){3,9}\.$", s) and unk >= 0.5:
        return "ПРОВЕРКА?"        # похоже на настоящую проверку - не вносим
    return "обычный" if unk <= 0.34 else "неясный"


rows = [(kind(s), n, s) for s, n in cnt.most_common()]
good = [r for r in rows if r[0] == "обычный"]
with open(os.path.join(OUT, "кандидаты.txt"), "w", encoding="utf-8") as f:
    for k, n, s in rows:
        f.write("%-9s %3d  %s\n" % (k, n, s))
print("обычный текст (в словарь):", len(good), "| похоже на проверку:", sum(1 for r in rows if r[0] == "ПРОВЕРКА?"), "| неясных:", sum(1 for r in rows if r[0] == "неясный"))

if "--apply" in sys.argv and good:
    import shutil
    shutil.copy(SHARED, SHARED + ".bak_%s" % time.strftime("%Y%m%d_%H%M"))
    add = ["\t/ в [а-яё ]+ состоянии\\./,", "\t/ тяжело вздохнул\\./,", "\t/^Раны [А-Яа-я]+ закрылись\\./,"]
    for k, n, s in good:
        if re.search(r" в [а-яё ]+ состоянии\.$", s) or s.endswith("тяжело вздохнул.") or re.match(r"^Раны \S+ закрылись\.$", s):
            continue                       # собрано обобщёнными шаблонами выше (имена мобов/игроков меняются)
        add.append("\t/" + re.sub(r"([.*+?^${}()|[\]\\/])", r"\\\1", s) + "/,")
    i = src.rindex("];")
    # вставляем до последней запятой массива (иначе пустой элемент-«дыра» остановит цикл while(InspectionWords[i]))
    head = src[:i].rstrip()
    if head.endswith(","):
        head = head[:-1]
    new = head + ",\n\t// --- Claude 12.11: обычный текст игры (ложные ПнП) ---\n" + "\n".join(add).rstrip(",") + "\n" + src[i:]
    open(SHARED, "wb").write(new.encode("cp1251", "replace"))
    print("записано в", SHARED, ":", len(add), "строк")
