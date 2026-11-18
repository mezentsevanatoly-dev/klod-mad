"""Зона целиком для Тадии (группа с Зороном): возврат -> Гален -> аватара -> Ривенделл -> спидволк -> область -> маршрут Чвырла.

python tools/run_zone.py <амон|пустоши> [с_шага] [до_шага]
Стоп, если что-то не так (нет пути, область не создалась, проходчик встал) — дальше вручную.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

AREAS = r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"
ZONES = {   # спидволк от портала Ривенделла 500001, комната входа, команда области, файл Чвырлы, шаг маршрута после входа
    # grp — строка группе перед созданием («гг !<grp> +1»: +1 — максимум для зон Ривенделла, польз.);
    # lvls — уровни сложности для самой команды области, от большего к меньшему (как в ботах Чвырлы)
    "амон": dict(sw="2ws3w5n2ws2wsw2sws5wn6wn3w2n5ws7ws3ws2ws3ws2w3nen", end="506022", create="обл соз север",
                 grp="обл с с", lvls=("+1", ""), name="рр5_АмонСул", first=2, stop=None),
    "омории": dict(sw="wwseeseesssswswssswssswswsswsswswsswsseseeseseeneee", end="505034", create="обл с в",
                   grp="обл с в", lvls=("+1", ""),
                   name="рр5_Мория", first=0, stop=370),       # Окрестности Мории; шаг 370 — вход в Морию (502014)
    "пустоши": dict(sw="2ws3w5n2ws2wsw2sws5wn3w2nw2ne4nw2ne2n2w", end="506018", create="обл соз север",
                    grp="обл с с", lvls=("+1", ""),
                    name="рр5_Пустоши", first=0, stop=108),     # до Зала магии бурь (дальше — ласт, соло не берётся)
}

NOREST = "--norest" in sys.argv                                         # без отдыха перед дорогой (польз.: «иди сразу»)
sys.argv = [a for a in sys.argv if a != "--norest"]
LAT = {"amon": "амон", "omories": "омории", "pustoshi": "пустоши"}     # латиницей — для запуска из терминала Claude
key = LAT.get(sys.argv[1], sys.argv[1])
Z = ZONES[key]
BOTP, MOBS = os.path.join(AREAS, Z["name"] + ".botp"), os.path.join(AREAS, Z["name"] + "_mob.csv")
w = b.Walker(b.load_mobs(MOBS))
w.last_msdp_from_log()


def say(*a):
    print(*a, flush=True)


def hp_full():
    out = w.answer("оч", 1.2)
    for l in out:
        m = re.search(r"Вы имеете (\d+)\((\d+)\) здоровья, (\d+)\((\d+)\) маны", l)
        if m:
            return int(m.group(1)) >= 0.95 * int(m.group(2)) and int(m.group(3)) >= 0.9 * int(m.group(4))
    return True


OPP = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"}


def reverse_sw(sw):
    """Спидволк обратно: «2ws3w» -> «3e2es» (порядок наоборот, направления противоположные)."""
    return "".join(f"{n}{OPP[d]}" for n, d in reversed(re.findall(r"(\d*)([nsewud])", sw)))


def path_to(room, tries=6):
    """Игровой «путь»: на закрытой двери встаёт, двери открывает триггер — повторяем."""
    for _ in range(tries):
        out = w.answer_until(f"путь {room}",     # отказ игры («не найдена») — выходим сразу, без 30-секундного ожидания
                             "достигли пункта назначения|уже находитесь в этой комнате|не найден|Нет пути|нет пути", 30)
        if any("достигли пункта назначения" in l or "уже находитесь в этой комнате" in l for l in out):
            return True
        time.sleep(0.5)
    return False


start = int(sys.argv[2]) if len(sys.argv) > 2 else None
stop = int(sys.argv[3]) if len(sys.argv) > 3 else Z["stop"]
if start is None:                                         # польз.: никаких отдыхов/пауз перед дорогой — сразу в путь
    if w.cur["area"] not in ("Гален", "Город Геолант", "Ривенделл", "Перекресток миров") and not w.cur["area"].startswith("Великий"):
        w.move_cmd("колд сл.возв", 5)                      # слово возврата -> Гален (рента)
        w.last_msdp_from_log()
        say(f"возврат: {w.cur['area']} {w.cur['name']}")
    if w.cur["area"] in ("Гален", "Город Геолант"):
        if not path_to("ава"):                            # «Портал в пустоту» рядом с Аватарой
            sys.exit("не дошла до аватары")
        import travel
        left = travel.gather(w)                            # польз.: призывать надо ЗДЕСЬ, у Аватары (90001) `!магия`
        if left:
            sys.exit("не собрались у портала: " + ", ".join(left))
        w.move_cmd("войти портал", 6)
        w.c.send("сня 10000")                              # дефолт (польз.): на руках 0, деньги в банке
        w.pump(0.5)
        w.move_cmd("куп 2", 8)                             # перенос ГРУППЫ (10000); «куп 1» — только если один в группе
        if not path_to("ривенделл"):
            sys.exit("не дошла до портала в Ривенделл")
        w.move_cmd("войти портал", 6)
    if w.cur["area"] == "Перекресток миров":                  # стоим у Аватары (группа уже оплачена `куп 2`): в портал Ривенделла
        if not path_to("ривенделл"):
            sys.exit("не дошла до портала в Ривенделл")
        w.move_cmd("войти портал", 6)
        w.last_msdp_from_log()
    home = next((z for z in ZONES.values() if z is not Z and z["end"] == w.cur["vnum"]), None)
    if home:                                               # стоим у входа в соседнюю зону: напрямую (Амон и Пустоши рядом, польз.)
        ta, tz = (re.findall(r"\d*[nsewud]", s["sw"]) for s in (home, Z))
        k = 0
        while k < min(len(ta), len(tz)) and ta[k] == tz[k]:   # общий отрезок пути от портала Ривенделла не проходим
            k += 1
        direct = reverse_sw("".join(ta[k:])) + "".join(tz[k:])
        w.check_group()
        if not w.speedwalk(direct, Z["end"]):
            sys.exit(f"прямой спидволк не дошёл: {w.cur}")
    else:
        if w.cur["vnum"] != "500001":
            if not path_to("магический портал"):
                sys.exit(f"не дошла до портала Ривенделла: {w.cur}")
        w.check_group()
        if not w.speedwalk(Z["sw"], Z["end"]):             # спидволк пачкой
            sys.exit(f"спидволк не дошёл: {w.cur}")
    made = lambda out: any(re.search(r"Создан экземпляр|создал\w* экземпляр зоны", l) for l in out)   # noqa: E731
    members = {n.lower() for n in w.group_state()}
    if members <= {"тадия", "зорон"}:                      # польз.: в группе только я и Зорон — создаём сами, без сложности
        out = w.answer(Z["create"], 3)
        say(" | ".join(l for l in out if l.strip())[:200])
        if not made(out):
            sys.exit("область не создалась")
    else:                                                  # иначе — только группе, максимальная сложность (при отказе — ниже)
        for lvl in Z["lvls"]:
            out = w.answer(f"гг !{Z['grp']} {lvl}".rstrip(), 4)    # Карис: «создала экземпляр»
            say(" | ".join(l for l in out if l.strip())[:200])
            if made(out):
                break
        else:
            sys.exit("область не создалась")
    w.to_group(["гг !агри"])                               # польз.: после создания области
    w.charge_staff()
    start = Z["first"]
sys.argv = [sys.argv[0], BOTP, MOBS, str(start)] + ([str(stop)] if stop else [])
b.main()
w.to_group(["гг !очистить", "гг !неагри"])                 # польз.: после окончания зоны
say(f"{key}: проход закончен")
