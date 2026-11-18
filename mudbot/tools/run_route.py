"""Зона по маршруту из areas/routes/zones.json: дойти до клетки создания (goto по картам) -> собрать группу -> создать область ->
`гг !агри` -> маршрут (botp_walk) -> `гг !очистить; гг !неагри`.

python tools/run_route.py <ключ> [шаг]
Правило создания (польз.): в группе только Тадия и Зорон — создаём сами «обл соз <напр>» без сложности; иначе — только группе
«гг !обл с <напр> +<сложность>», от большей к меньшей (список lvls). Без отдыхов и пауз: сразу в путь.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

CFG = os.path.join(os.path.dirname(HERE), "areas", "routes", "zones.json")
key = sys.argv[1]
Z = json.load(open(CFG, encoding="utf-8"))[key]
start = int(sys.argv[2]) if len(sys.argv) > 2 else None
if not Z.get("mobs"):                                   # нет csv мобов Чвырлы — пустая таблица (цели берём по тексту клетки)
    Z["mobs"] = os.path.join(os.path.dirname(CFG), "_empty_mob.csv")
    if not os.path.exists(Z["mobs"]):
        open(Z["mobs"], "w", encoding="cp1251").write("Описание в комнате;Имя моба;Уровень;Флаги NPC\n")
w = b.Walker(b.load_mobs(Z["mobs"]))
w.last_msdp_from_log()


def say(*a):
    print(*a, flush=True)


if start is None:
    if Z.get("city") and w.cur["area"] != Z["city"]:       # другой город: через Аватару (`путь ава` -> сбор группы у портала -> `!tp`)
        import travel
        from goto import goto
        if "Портал в пустоту" not in w.cur["name"]:
            say(f"в {Z['city']} через Аватару, сейчас {w.cur['area']} {w.cur['name']}")
            out = w.answer_until("путь ава", "достигли пункта назначения|уже находитесь в этой комнате|не найден", 30)
            w.last_msdp_from_log()
        if not travel.main(Z["city_key"]):
            sys.exit("переезд в город не удался")
        w.last_msdp_from_log()
    if w.cur["vnum"] != Z["outer"]:
        from goto import goto
        say(f"иду к клетке создания {Z['outer']} из {w.cur['vnum']} {w.cur['name']}")
        goto(w, Z["outer"])
        w.last_msdp_from_log()
        if w.cur["vnum"] != Z["outer"]:
            sys.exit(f"не дошла до клетки создания: {w.cur}")
    w.check_group()
    made = lambda out: any(re.search(r"Создан экземпляр|создал\w* экземпляр зоны", l) for l in out)   # noqa: E731
    members = {n.lower() for n in w.group_state()}
    if members <= {"тадия", "зорон"}:
        out = w.answer(Z["create"], 3)
        say(" | ".join(l for l in out if l.strip())[:200])
        if not made(out):
            sys.exit("область не создалась")
    else:
        for lvl in Z["lvls"]:
            out = w.answer(f"гг !{Z['grp']} {lvl}".rstrip(), 4)
            say(" | ".join(l for l in out if l.strip())[:200])
            if made(out):
                break
        else:
            sys.exit("область не создалась")
    w.to_group(["гг !агри"])
    w.charge_staff()
    for c in Z.get("pre", []):                              # вход в зону из клетки создания (например «запад»), когда его нет в маршруте
        w.move_cmd(c, 6)
        w.last_msdp_from_log()
    start = Z.get("first", 0)
sys.argv = [sys.argv[0], Z["botp"], Z["mobs"], str(start)] + ([str(Z["stop"])] if Z.get("stop") else [])
b.main()
w.to_group(["гг !очистить", "гг !неагри"])
say(f"{key}: проход закончен")
