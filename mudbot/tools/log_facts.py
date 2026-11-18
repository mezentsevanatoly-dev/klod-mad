# -*- coding: utf-8 -*-
"""Полный проход по ВСЕМ логам (JMC пользователя, логи обеих жаб, архив, mudbot) и сбор фактов:
смерти+контекст, холдеры (кто какое заклинание), сбивания с ног, ассисты, двери/ключи, возвраты вещей на склад, лвл-апы, заклинания мобов.
Результат: mudbot/data/recon/ВСЕ_ЛОГИ/{факты.md, смерти.md, холдеры.csv, заклинания_мобов.csv, ассисты.csv, двери.csv, возвраты.csv}.
Ничего не отправляет в игру. Запуск: python -X utf8 tools/log_facts.py"""
import os, re, sys, glob, collections, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "recon", "ВСЕ_ЛОГИ"); os.makedirs(OUT, exist_ok=True)
SKIP_EXT = {".exe", ".dll", ".rar", ".ini", ".set", ".bat", ".dat", ".png", ".webp", ".zip", ".db", ".json", ".pyc"}
roots = [os.path.join(BASE, "JMC"), os.path.join(BASE, "JMC БОТ АЙЛИНА", "Logs"), os.path.join(BASE, "JMC БОТ ИНКА", "Logs"),
         os.path.join(BASE, "JMC БОТ АЙЛИНА"), os.path.join(BASE, "JMC БОТ ИНКА"), os.path.join(BASE, "_архив_мад"),
         os.path.join(BASE, "Тадия_старая_копия_03.11"), ROOT]
files = []; seen = set()
for r in roots:
    for dp, dn, fn in os.walk(r):
        if any(x in dp for x in ("\\wiki", "\\help", "\\.git", "__pycache__", "\\ВСЕ_ЛОГИ", "\\scripts", "\\areas")):
            continue
        for f in fn:
            p = os.path.join(dp, f); ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT or f.endswith(".bak") or ".bak_" in f:
                continue
            if not (ext in (".log", ".txt", "") or f.startswith("game_") or "log" in f.lower()):
                continue
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz < 2000:
                continue
            key = (f, sz)
            if key in seen:
                continue
            seen.add(key); files.append(p)
print("файлов:", len(files), flush=True)


def lines_of(p):
    b = open(p, "rb").read()
    try:
        t = b.decode("utf-8")
        if "�" in t[:200000]:
            raise UnicodeDecodeError("x", b"", 0, 1, "x")
    except UnicodeDecodeError:
        t = b.decode("cp1251", "replace")
    return t.splitlines()


TS = re.compile(r"^\[?\d\d:\d\d:\d\d\]? ?")
SPELL = re.compile(r"^(.+?) произнес(?:ла|ло|ли)? магические слова '([^']+)'")
HOLD = re.compile(r"придержать|не в силах шевельнуться|замер(?:ла|ло|ли)? на месте|Вы замерли|оковы тьмы|оцепенен", re.I)
KD = re.compile(r"сбил\w* (?:вас )?с ног|Вы полетели на землю|Ударная волна сбила|подножк|упал\w* и больно ударил", re.I)
ASSIST = re.compile(r"^(.+?) вступил\w* в бой на стороне (.+?)\.?$")
DEAD = re.compile(r"Вы мертвы|Вы умерли|R\.I\.P\.\s*$")
DOOR = re.compile(r"Вы (?:отперли|открыли|отпер)|заперт|Попробуйте сначала открыть|ключ", re.I)
RET = re.compile(r"вернул\w* на ваш склад|вернулись? на склад")
LVL = re.compile(r"Вы поднялись на уровень|Вы достигли \d+ уровня|вы стали (\d+) уровня")
cnt = collections.Counter(); spells = collections.Counter(); holds = collections.Counter(); kds = collections.Counter()
assists = collections.Counter(); doors = collections.Counter(); rets = []; deaths = []; lvls = collections.Counter()
t0 = time.time(); nlines = 0
for p in files:
    L = lines_of(p); nlines += len(L); fn = os.path.relpath(p, BASE)
    ctx = collections.deque(maxlen=25)
    for i, s0 in enumerate(L):
        s = TS.sub("", s0).strip()
        ctx.append(s)
        if not s:
            continue
        m = SPELL.match(s)
        if m and not m.group(1).startswith("Вы"):
            spells[(m.group(1).strip(), m.group(2))] += 1
            if HOLD.search(m.group(2)):
                holds[(m.group(1).strip(), m.group(2))] += 1
        if HOLD.search(s) and not m:
            cnt["холд-строк"] += 1
        if KD.search(s):
            kds[re.sub(r"\[\d+\]|\.\.\.", "", s)[:90]] += 1
        a = ASSIST.match(s)
        if a:
            assists[(a.group(1).strip(), a.group(2).strip())] += 1
        if DOOR.search(s) and len(s) < 140:
            doors[s[:110]] += 1
        if RET.search(s):
            rets.append((fn, s[:120]))
        if re.search(r"Вы мертвы", s):
            deaths.append((fn, i + 1, list(ctx)))
        if LVL.search(s):
            lvls[fn] += 1
        if s.startswith("Вы получили") and "опыта" in s:
            cnt["убийств с опытом"] += 1
    print(round(time.time() - t0), "с", fn, len(L), flush=True)
with open(os.path.join(OUT, "заклинания_мобов.csv"), "w", encoding="utf-8") as f:
    f.write("кто;заклинание;раз\n")
    for (w, sp), n in spells.most_common():
        f.write("%s;%s;%d\n" % (w, sp, n))
with open(os.path.join(OUT, "холдеры.csv"), "w", encoding="utf-8") as f:
    f.write("кто;чем холдит;раз\n")
    for (w, sp), n in holds.most_common():
        f.write("%s;%s;%d\n" % (w, sp, n))
with open(os.path.join(OUT, "ассисты.csv"), "w", encoding="utf-8") as f:
    f.write("кто;на чьей стороне;раз\n")
    for (w, sp), n in assists.most_common(3000):
        f.write("%s;%s;%d\n" % (w, sp, n))
with open(os.path.join(OUT, "двери.csv"), "w", encoding="utf-8") as f:
    f.write("строка;раз\n")
    for s, n in doors.most_common(1500):
        f.write("%s;%d\n" % (s.replace(";", ","), n))
with open(os.path.join(OUT, "возвраты.csv"), "w", encoding="utf-8") as f:
    f.write("файл;строка\n")
    for fn, s in rets[:3000]:
        f.write("%s;%s\n" % (fn, s.replace(";", ",")))
with open(os.path.join(OUT, "смерти.md"), "w", encoding="utf-8") as f:
    f.write("# Смерти («Вы мертвы») со 25 строками контекста до\n\n")
    for fn, ln, c in deaths:
        f.write("## %s:%d\n```\n%s\n```\n" % (fn, ln, "\n".join(c[-22:])))
with open(os.path.join(OUT, "факты.md"), "w", encoding="utf-8") as f:
    f.write("# Факты из всех логов (программный проход)\nфайлов: %d, строк: %d, время %d с\n\n" % (len(files), nlines, time.time() - t0))
    f.write("убийств с опытом: %d | смертей: %d | возвратов вещей: %d | лвл-апов: %d\n\n" % (cnt["убийств с опытом"], len(deaths), len(rets), sum(lvls.values())))
    f.write("## Топ холдеров (мобы, кастующие холд)\n")
    for (w, sp), n in holds.most_common(60):
        f.write("- %s: %s ×%d\n" % (w, sp, n))
    f.write("\n## Топ «сбили с ног»\n")
    for s, n in kds.most_common(40):
        f.write("- %s ×%d\n" % (s, n))
    f.write("\n## Топ ассистов\n")
    for (w, sp), n in assists.most_common(40):
        f.write("- %s -> %s ×%d\n" % (w, sp, n))
    f.write("\n## Файлы\n")
    for p in files:
        f.write("- %s\n" % os.path.relpath(p, BASE))
print("ГОТОВО: файлов", len(files), "строк", nlines, "смертей", len(deaths), flush=True)
