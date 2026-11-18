"""Мория (502) для Тадии с Зороном по маршруту Чвырла рр5_Мория.botp — этапами, с условиями и повторами кругов.

python tools/run_moria.py [номер_этапа ...]        без аргументов — все этапы подряд, стоп при первой неудаче
Этапы (индексы шагов маршрута; см. tools/moria_map.py):
 1 ямы           370-401   гарпун затягивает в яму -> нужен «уголок ключа-звезды» с орка-ловчего; нет — круг заново с 385
 2 коридоры      401-524   до разрушенного тоннеля 502065
 3 тоннель, лом  524-560   решётки; нужен «тяжелый гномий лом» с олог-хая дебошира; нет — круг заново с 527
 4 кузни, маг    560-640   Седой маг бродит: круг с 590, пока не «Седой маг мертв»
 5 тени          640-693   инфразрение, огл-скан, тени
 6 склянка гному 693-738   (дать скля.с.зат.тен древ.гном.б.т на шаге 710)
 7 статуи, гроб. 738-768   разрушить статуи, гробница Балина (книга)
 8 испытание     768-779   снять оружие, пройти, надеть
 9 мост          779-788   скинуть книгу — балрог — упасть в бездну — убить — скинуть книгу
АСТРАЛЬНАЯ ГОПА (запад от 502084) — не трогать (польз.).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

AREAS = r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"
BOTP, MOBS = os.path.join(AREAS, "рр5_Мория.botp"), os.path.join(AREAS, "рр5_Мория_mob.csv")
steps = b.load_steps(BOTP)
w = b.Walker(b.load_mobs(MOBS))
w.last_msdp_from_log()


def say(*a):
    print(*a, flush=True)


def inv_has(sub):
    return any(sub in l.lower() for l in w.answer("инв", 1.2))


OUTLOG = os.path.join(os.path.dirname(HERE), "out.log")


def hist_has(sub, since):
    """since — байтовое смещение в out.log (w.bot.history обрезается до 400 строк, индексы врут)."""
    with open(OUTLOG, "rb") as f:
        f.seek(since)
        return sub in f.read().decode("utf-8", "replace")


STAGES = {
    1: dict(name="ямы", a=370, b=401, need="уголок", redo=385),
    2: dict(name="коридоры", a=401, b=524),
    3: dict(name="тоннель и лом", a=524, b=560, need="лом", redo=527),
    4: dict(name="кузни и Седой маг", a=560, b=640, hist="Седой маг мертв", redo=590),
    5: dict(name="тени", a=645, b=693),
    6: dict(name="склянка гному", a=693, b=738),
    7: dict(name="статуи и гробница", a=738, b=768),
    8: dict(name="испытание", a=774, b=779),
    9: dict(name="мост", a=779, b=788),
}


def pits():
    """Ямы: гарпун затягивает случайного игрока в 502201, там орк-ловчий роняет уголок ключа. Кружим по ямам, пока не затянет."""
    w.pump(1)
    if int(w.cur["vnum"]) == 502040:
        b.walk(w, steps, 388, 389)  # юг в 502041
    for rnd in range(25):
        if inv_has("уголок"):
            say("уголок есть")
            break
        if int(w.cur["vnum"]) == 502201:
            say("затянуло на дно ямы — бой")
            for _ in range(8):
                w.fight_here()
                w.c.send("взять все")
                w.pump(2)
                foes, _ = w.classify()
                if not foes:
                    break
            if inv_has("уголок"):
                w.c.send("вверх")
                w.pump(3)
                break
            continue
        if rnd and rnd % 2 == 0:
            # затянутого гарпуном зовём в приват: пусть он призывает НАС (в гг призовут все)
            for l in w.answer("пгр", 1.5):
                if "Зорон" in l and " Н " in l.split("Зорон", 1)[1][:30].replace("  ", " ")[:12]:
                    w.c.send("ск зорон !к призыв тадия")
                    w.pump(3)
                    break
        say(f"круг по ямам {rnd}")
        b.walk(w, steps, 390, 402)
        w.pump(3)
    return inv_has("уголок")


def run_stage(n):
    st = STAGES[n]
    if n == 1:
        w.pump(1)
        if 502041 <= int(w.cur["vnum"]) <= 502048 or int(w.cur["vnum"]) == 502201:
            return pits()
        i = b.walk(w, steps, st["a"], 389)
        if i < 388:
            say(f"остановилась на {i}")
            return False
        return pits()
    say(f"=== этап {n}: {st['name']} ({st['a']}-{st['b']})")
    t0 = os.path.getsize(OUTLOG)
    first = steps[st["a"]]
    if first[0] == "step" and str(w.cur["vnum"]) != first[1]:
        from goto import goto, world
        if not goto(w, first[1], world()):
            say("не дошла до начала этапа")
            return False
    i = b.walk(w, steps, st["a"], st["b"])
    if i < st["b"]:
        say(f"этап {n}: остановилась на шаге {i} — дальше вручную")
        return False
    for attempt in range(1, 6):
        ok = True
        if st.get("need") and not inv_has(st["need"]):
            ok = False
        if st.get("hist") and not hist_has(st["hist"], t0):
            ok = False
        if ok:
            say(f"этап {n}: условие выполнено")
            return True
        say(f"этап {n}: условия нет (круг {attempt}) — повторяю с шага {st['redo']}")
        # вернуться к началу круга: идём к комнате шага redo по картам и повторяем отрезок
        from goto import goto, world
        if not goto(w, steps[st["redo"]][1], world()):
            say("не дошла до начала круга")
            return False
        i = b.walk(w, steps, st["redo"], st["b"])
        if i < st["b"]:
            say(f"этап {n}: остановилась на шаге {i}")
            return False
    say(f"этап {n}: условие так и не выполнено")
    return False


todo = [int(x) for x in sys.argv[1:]] or list(STAGES)
for n in todo:
    if not run_stage(n):
        break
say("конец")

