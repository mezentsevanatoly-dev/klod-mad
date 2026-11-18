"""Амон Сул целиком (Тадия): отдых, посох, Гален -> аватара -> Ривенделл -> спидволк -> область -> маршрут Чвырла.

python tools/run_amon.py [с_шага_маршрута]
Останавливается, если что-то пошло не так (нет пути, не создалась область, проходчик встал) — дальше вручную.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

AREAS = r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"
BOTP, MOBS = os.path.join(AREAS, "рр5_АмонСул.botp"), os.path.join(AREAS, "рр5_АмонСул_mob.csv")
SW = "2ws3w5n2ws2wsw2sws5wn6wn3w2n5ws7ws3ws2ws3ws2w3nen"     # портал Ривенделла 500001 -> 506022
FIRST = 2                                                    # шаги 0-1 маршрута — подход к 506022

w = b.Walker(b.load_mobs(MOBS))
w.last_msdp_from_log()


def say(*a):
    print(*a, flush=True)


def path_to(room, tries=6):
    """Игровой «путь»: на закрытой двери он встаёт, двери открывает триггер бота — просто повторяем."""
    for _ in range(tries):
        out = w.answer(f"путь {room}", 30)
        if any("достигли пункта назначения" in l or "уже находитесь в этой комнате" in l for l in out):
            return True
        time.sleep(2)
    return False


def rest_full():
    st = w.bot.status
    if st and st.hp >= 0.95 * w.bot.max_hp:
        return
    w.cast_cd("регенерация", "колд регенерация")     # польз.: регенерацию кастуем вместе с расслаблением
    w.answer("отдыхать", 1)
    w.answer("расслабиться", 1.5)
    t0 = time.time()
    while time.time() - t0 < 300:
        w.pump(5)
        st = w.bot.status
        if st and st.hp >= 0.95 * w.bot.max_hp and st.mp >= 0.9 * 16944:
            break
    w.answer("вст", 1)
    say(f"отдых: HP {w.bot.status.hp if w.bot.status else '?'}")


def charge_staff():
    for c in ("сня 18.", "од роза", "посох", "од все"):          # польз.: 18. = левая рука (тотем) -> роза -> посох -> тотем обратно
        w.answer(c, 1.2)
    say("посох заряжен")


start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if start == 0:
    rest_full()
    if w.cur["area"] == "Гален":
        if not path_to("ава"):
            sys.exit("не дошла до аватары")
        w.answer("войти портал", 4)
        w.c.send("сня 10000")            # дефолт (польз.): на руках 0, деньги в банке; у аватары есть услуги банка
        w.c.send("куп 2")                # перенос ГРУППЫ (10000): «куп 1» — только если в группе один персонаж
        w.pump(6)
        if not path_to("ривенделл"):
            sys.exit("не дошла до портала в Ривенделл")
        w.answer("войти портал", 4)
    if w.cur["vnum"] != "500001":
        if not path_to("магический портал"):
            sys.exit(f"не дошла до портала Ривенделла: {w.cur}")
    if not w.speedwalk(SW, "506022"):                          # спидволк пачкой, весь путь одной очередью
        sys.exit(f"спидволк не дошёл: {w.cur}")
    w.to_group(["гг !обл с с +1"])                             # польз.: перед созданием области — сложность экземпляра группе
    out = w.answer("обл соз север", 3)
    say(" | ".join(l for l in out if l.strip())[:200])
    if not any("Создан экземпляр" in l for l in out):
        sys.exit("область не создалась")
    charge_staff()
    start = FIRST
sys.argv = [sys.argv[0], BOTP, MOBS, str(start)]
b.main()
say("Амон Сул: проход закончен")
