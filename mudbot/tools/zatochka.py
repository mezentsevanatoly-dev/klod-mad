"""Журнал заточки (держится 8 часов): Клод мад\\ЗАТОЧКА.csv
python -X utf8 tools/zatochka.py статус                       -> последние заточки и сколько осталось
python -X utf8 tools/zatochka.py запись <персонаж> <оружие>   -> записать заточку сейчас
Правило: ПРАВИЛА\\ЗАТОЧКА.md"""
import os, sys, datetime

HOURS = 8
FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ЗАТОЧКА.csv")
FMT = "%d.%m.%Y %H:%M"
HEAD = "заточено;персонаж;оружие;кончится\n"


def rows():
    if not os.path.exists(FILE):
        return []
    with open(FILE, encoding="utf-8-sig") as f:
        return [l.rstrip("\n").split(";") for l in f.readlines()[1:] if l.strip()]


def status():
    now = datetime.datetime.now()
    last = {}
    for r in rows():
        last[(r[1], r[2])] = r
    if not last:
        print("заточек в журнале нет — точить можно")
        return
    for (who, wpn), r in last.items():
        end = datetime.datetime.strptime(r[3], FMT)
        if end > now:
            left = end - now
            print("%s %s: заточено %s, держится ещё %d ч %02d мин (до %s) — НЕ ТОЧИТЬ"
                  % (who, wpn, r[0], left.seconds // 3600 + left.days * 24, left.seconds % 3600 // 60, r[3]))
        else:
            print("%s %s: заточено %s, кончилось %s — можно точить" % (who, wpn, r[0], r[3]))


def add(who, wpn):
    now = datetime.datetime.now()
    new = not os.path.exists(FILE)
    with open(FILE, "a", encoding="utf-8-sig" if new else "utf-8") as f:
        if new:
            f.write(HEAD)
        f.write("%s;%s;%s;%s\n" % (now.strftime(FMT), who, wpn, (now + datetime.timedelta(hours=HOURS)).strftime(FMT)))
    print("записано:", who, wpn, now.strftime(FMT), "-> до", (now + datetime.timedelta(hours=HOURS)).strftime(FMT))


if len(sys.argv) >= 2 and sys.argv[1] in ("статус", "status"):
    status()
elif len(sys.argv) >= 4 and sys.argv[1] in ("запись", "add"):
    add(sys.argv[2], " ".join(sys.argv[3:]))
else:
    print(__doc__)
