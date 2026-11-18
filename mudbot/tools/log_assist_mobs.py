# -*- coding: utf-8 -*-
"""Словарь МОБОВ-АССИСТОВ из всех логов: моб X помогает мобу Y (вступил в бой на стороне / героически спас / попытался спасти).
Результат: mudbot/data/ассист_мобы.csv (моб;раз помог;кому помогал (топ);где). Только чтение логов."""
import os, re, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "ассист_мобы.csv")
ANSI = re.compile(r"\x1b\[[0-9;]*m|\[\d+(?:;\d+)*m")
PLAYERS = {"вы", "зорон", "кейб", "карис", "сьерон", "съезо", "штыра", "мряка", "мералион", "барг", "элронг", "денар", "айлина", "кимпи", "тадия", "эсхирд", "ждадиус", "даркро", "ваарт", "олирон", "камелия"}
files = []; seen = set()
for r in (os.path.join(BASE, "JMC"), os.path.join(BASE, "JMC БОТ АЙЛИНА", "Logs"), os.path.join(BASE, "JMC БОТ ИНКА", "Logs"), os.path.join(BASE, "_архив_мад")):
    for dp, dn, fn in os.walk(r):
        for f in fn:
            p = os.path.join(dp, f); ext = os.path.splitext(f)[1].lower()
            if ext in (".exe", ".dll", ".rar", ".ini", ".set", ".bat", ".dat", ".png", ".webp", ".zip", ".json", ".py", ".md", ".csv"):
                continue
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz < 5000 or (f, sz) in seen:
                continue
            seen.add((f, sz)); files.append(p)
for j in ("JMC БОТ АЙЛИНА", "JMC БОТ ИНКА"):
    p = os.path.join(BASE, j, "claude_game.log")
    if os.path.exists(p) and (os.path.basename(p), os.path.getsize(p)) not in seen:
        seen.add((os.path.basename(p), os.path.getsize(p))); files.append(p)
A = re.compile(r"^(?P<x>[А-ЯЁ][^.!?\[]{2,45}?) вступил\w* в бой на стороне (?P<y>[^.!?\[]+?)[.!]?\s*$")
B = re.compile(r"^(?P<x>[А-ЯЁ][^.!?\[]{2,45}?) (?:героически )?спас(?:ла|ло|ли)? (?P<y>[^.!?\[]+?) от (?P<z>[^.!?\[]+?)!")
C = re.compile(r"^(?P<x>[А-ЯЁ][^.!?\[]{2,45}?) попытал\w+ спасти (?P<y>[^.!?\[]+?) от (?P<z>[^.!?\[]+?),")
cnt = collections.Counter(); helped = collections.defaultdict(collections.Counter); where = collections.defaultdict(collections.Counter)


def is_mob(n):
    n = n.strip()
    w = n.lower().split()
    if not w or w[0] in PLAYERS or n.lower() in PLAYERS:
        return False
    return len(w) >= 2 or n.endswith(("а", "я", "ь", "к", "н", "р", "т", "л", "с", "ц")) and n.lower() not in PLAYERS


for p in files:
    try:
        t = open(p, "rb").read()
        try:
            t = t.decode("utf-8")
            if "�" in t[:100000]:
                raise ValueError
        except Exception:
            t = t.decode("cp1251", "replace")
    except OSError:
        continue
    zone = os.path.basename(p)
    for s in t.splitlines():
        s = ANSI.sub("", re.sub(r"^\[?\d\d:\d\d:\d\d\]? ?", "", s)).strip()
        if len(s) < 12 or len(s) > 160:
            continue
        m = A.match(s) or B.match(s) or C.match(s)
        if not m:
            continue
        x, y = m.group("x").strip(), m.group("y").strip()
        if not is_mob(x) or y.lower() in PLAYERS or y.lower().rstrip("аыуе") in PLAYERS or y.startswith("ва") and len(y) < 6:
            continue
        cnt[x] += 1; helped[x][y] += 1; where[x][zone] += 1
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    f.write("моб-ассист;раз помог;кому помогал (топ-3);где (топ-3 лога)\n")
    for x, n in cnt.most_common():
        f.write("%s;%d;%s;%s\n" % (x, n, " / ".join(k for k, _ in helped[x].most_common(3)), " / ".join(k for k, _ in where[x].most_common(3))))
print("файлов", len(files), "мобов-ассистов", len(cnt))
for x, n in cnt.most_common(40):
    print("%-40s %4d  -> %s" % (x, n, ", ".join(k for k, _ in helped[x].most_common(2))))
