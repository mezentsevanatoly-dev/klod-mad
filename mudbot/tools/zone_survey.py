"""Разведка зон от низкого уровня к высокому: вход -> область -> обход с осмотром мобов по номерам и боем -> рекол домой.

  python tools/zone_survey.py                 весь список ZONES
  python tools/zone_survey.py "Парк" "Аллея"  только указанные
Всё пишется в data/game.db: mob_cards (карточки), mob_kills (опыт за каждое убийство), journal (что и почему).
Бьёт мобов не выше свой уровень + 4 (правило пользователя: на 5 и больше выше не трогать).
"""
import os
import re
import sqlite3
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
DIRW = {"север": "север", "юг": "юг", "восток": "восток", "запад": "запад", "вверх": "вверх", "вниз": "вниз"}
# (зона в игре, как назвать вход в `путь вход в зону …`, нужна ли область, максимум минут)
ZONES = [
    ("Мад школа", "приемная", False, 6),
    ("Парк", "парк", True, 12),
    ("Аллея", "аллея", True, 12),
    ("Канализация", "канализация", True, 12),
    ("Притон", "притон", True, 14),
    ("Парк аттракционов", "парк аттракционов", True, 14),
    ("Порт Элендора", "порт элендора", True, 14),
    ("Здание стражи Элендора", "здание стражи", True, 12),
    ("Башня магов", "башня магов", True, 14),
    ("Развалины Элендора", "развалины", True, 14),
]
# Маршрут пользователя (data/incarnation_varvar_1_30.md): (зона, вход, область, минут, город входа). По разу каждого вида (--once).
ROUTE = [
    ("Катакомбы Геоланта", "", True, 14, "гео_цп"),
    ("Чайный домик", "", True, 8, "гео_цп"),
    ("Лагерь гоблинов", "", True, 10, "гео_цп"),
    ("Болото", "", True, 12, "элен_цп"),
]
PREP = {"Катакомбы Геоланта": ["отпер люк", "откр люк"], "Чайный домик": []}       # команды сразу после входа в зону (логи пользователя)
CITY = {"Геолант": ("гео", "Город Геолант"), "Огис": ("огис", "Город Огис")}


HUBV = {"элен_цп": "100009", "гео_цп": "115039", "фело_цп": "198005", "огис_цп": "180096"}


def walk_to(vnum):
    """Пешком до комнаты по графу rooms (спидволк через `!sw`), без `путь` и реколла."""
    import zone_entrances as ze
    cur = where()[0]
    if cur == vnum:
        return True
    p = ze.bfs(ze.graph(), cur, vnum)
    if not p:
        return False
    cmd([f"!sw {ze.compress(p)}"], max(20, len(p) * 1.2))
    return where()[0] == vnum


def enter_walk(zone, hub, need_area):
    """Зона по готовому спидволку `<хаб>-<Зона>_область` из БД: дойти, создать область, зайти."""
    import zone_entrances as ze
    zn = zone.replace(" ", "_")
    r = sqlite3.connect(DB).execute("select path,end_vnum,note from speedwalks where name=?", (f"{hub}-{zn}_область",)).fetchone()
    if not r:
        say(f"{zone}: нет спидволка {hub}-{zn}_область")
        return False
    if not walk_to(HUBV[hub]):
        say(f"{zone}: не дошла до {hub}")
        return False
    cmd([f"!sw {r[0]}"], 30)
    if where()[0] != r[1]:
        say(f"{zone}: на клетке входа {r[1]} не оказалась: {where()}")
        return False
    m = re.search(r"выход в зону: (\w+)", r[2])
    d = m.group(1)
    dn = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}[d]
    if need_area:
        say(f"{zone}: область:", re.sub(r"\s+", " ", cmd([f"обл соз {dn[:2] if dn in ('вверх', 'вниз') else dn[0]}"], 4))[-100:])
    cmd([dn], 3)
    return where()[1] == zone


def to_city(city):
    """Элендор -> конюшня -> `ехать <город>`; в Элендоре ничего не делаем (дом)."""
    if city == "Элендор":
        return go_home()
    word, area = CITY[city]
    if where()[1] == area:
        return True
    if not go_home():
        return False
    cmd(["путь конюшня"], 40)
    cmd([f"ехать {word}"], 12)
    time.sleep(3)
    return where()[1] == area


def say(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def journal(stage, chk, result, decision, why):
    c = sqlite3.connect(DB, timeout=20)
    c.execute("INSERT INTO journal (t,stage,chk,result,decision,why) VALUES (?,?,?,?,?,?)", (time.strftime("%d.%m %H:%M"), stage, chk, result, decision, why))
    c.commit()
    c.close()


def cmd(cmds, wait=2.0):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py")] + [f"{c}|{wait}" for c in cmds],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    return r.stdout


def where():
    o = cmd(["где"], 2)
    m = re.findall(r"\[cur\] \{'vnum': '(\d+)', 'area': '([^']*)', 'name': '([^']*)'", o.replace("\n", " "))
    return m[-1] if m else ("", "", "")


def go_home():
    for _ in range(3):
        if where()[1] == "Город Элендор":
            return True
        cmd(["зач охр"], 8)
        time.sleep(4)
    return where()[1] == "Город Элендор"


def enter(zone, entrance, need_area):
    o = cmd([f"путь вход в зону {entrance}" if zone != "Мад школа" else "путь приемная"], 60)
    for _ in range(3):
        if "Вы достигли пункта назначения" in o or "уже находитесь" in o:
            break
        o += cmd(["где"], 25)
    o = cmd(["смотреть"], 2)
    m = re.search(r"\[Зона, (?:на )?([а-я]+): " + re.escape(zone) + r",?", o)
    d = m.group(1) if m else ("север" if zone == "Мад школа" else None)
    if not d:
        say(f"{zone}: не вижу выход в зону в этой комнате")
        return False
    if need_area:
        t = cmd([f"обл соз {d[0]}"], 4)
        say(f"{zone}: область:", re.sub(r"\s+", " ", t)[-120:])
    cmd([d], 3)
    return where()[1] == zone


def main(only):
    sys.path.insert(0, os.path.join(HERE, "tools"))
    import gamedb
    gamedb._c().close()                                     # создать таблицы mob_cards / mob_kills, если их ещё нет
    say("старт разведки; дом:", where())
    route = "--route" in only
    only = [a for a in only if a != "--route"]
    todo = [(z, e, a, m, "Элендор") for z, e, a, m in ZONES] if not route else ROUTE
    for zone, entrance, need_area, minutes, city in todo:
        if only and zone not in only:
            continue
        if route:
            ok = enter_walk(zone, city, need_area)                  # city здесь = хаб (гео_цп, элен_цп…), без `путь` и реколла
        else:
            if not to_city(city):
                say(f"не удалось попасть в {city} — стоп")
                journal("разведка", f"город {city} перед зоной {zone}", "не там", "остановлено", "рекол/поездка не сработали")
                return
            ok = enter(zone, entrance, need_area)
        if not ok:
            journal("разведка", f"вход в {zone}", "не вошла", "зона пропущена", "нет выхода/области в этой комнате; разобрать вручную")
            say(f"{zone}: вход не удался, пропускаю")
            continue
        for pc in PREP.get(zone, []):                              # двери/люки из логов пользователя (mapfight сам не открывает)
            cmd([pc], 2)
        say(f"{zone}: вошла, разведка до {minutes} мин")
        k0 = sqlite3.connect(DB).execute("select count(*) from mob_kills where zone=?", (zone,)).fetchone()[0]
        c0 = sqlite3.connect(DB).execute("select count(*) from mob_cards where zone=?", (zone,)).fetchone()[0]
        env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
        p = subprocess.Popen([sys.executable, "-X", "utf8", os.path.join("tools", "mapfight.py"), "99", "--survey", "--zone", zone,
                              "--extra", "4", "--below", "99", "--skip", "0"] + (["--once"] if route else []), cwd=HERE, env=env,
                             stdout=open(os.path.join(HERE, "tools", f"run_survey_{zone.replace(' ', '_')}.log"), "w", encoding="utf-8"),
                             stderr=subprocess.STDOUT)
        t0 = time.time()
        while p.poll() is None and time.time() - t0 < minutes * 60:
            time.sleep(10)
        if p.poll() is None:
            p.kill()
        db = sqlite3.connect(DB)
        k1 = db.execute("select count(*) from mob_kills where zone=?", (zone,)).fetchone()[0]
        c1 = db.execute("select count(*) from mob_cards where zone=?", (zone,)).fetchone()[0]
        say(f"{zone}: убито {k1 - k0}, новых карточек {c1 - c0}, за {int(time.time() - t0) // 60} мин")
        journal("разведка", f"зона {zone}", f"убито {k1 - k0}, новых карточек мобов {c1 - c0}, {int(time.time() - t0) // 60} мин",
                "возврат реколом", "опыт и карточки записаны в mob_kills / mob_cards")
        if route:
            walk_to(HUBV[city])                                     # назад пешком по графу, не реколлом (польз. 03.11)
    if not route:
        go_home()
    say("разведка закончена")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])

