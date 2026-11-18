"""Ласт Пустошей троллей (Сердце бури 503102) для Тадии с группой (Зорон). Заходит из Зала магии бурь 503103.

python tools/storm_heart.py
Бой — fight_here (землетрясение, полиморф на лекарей, слепота/молчание/холд по аф, пронзание сердца лучом).
Отступает (убежать) при HP < 40% или мане < 4000.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

AREAS = r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"
w = b.Walker(b.load_mobs(os.path.join(AREAS, "рр5_Пустоши_mob.csv")))
w.last_msdp_from_log()
w.boss_fight = True                                # ласт: полиморф на лекарей разрешён


def flee():
    for _ in range(4):
        for c in ("очистить", "вст", "убежать"):
            w.c.send(c)
        w.pump(2.5)
        if w.cur["vnum"] != "503102":
            break
    print(f"отступила: {w.cur['vnum']} {w.cur['name']}", flush=True)


if w.cur["vnum"] == "503103":
    w.check_group()
    w.c.send("ск зорон !запад")                   # польз.: сначала Зорона в клетку к ласту — пусть его бьют первым
    w.pump(4.0)
    w.move("W")                                   # потом сама: подкр запад -> Сердце бури
print("вошла:", w.cur["vnum"], w.cur["name"], flush=True)
t0 = time.time()
try:
    for rnd in range(40):
        done = w.fight_here()
        st = w.bot.status
        print(f"раунд {rnd}: HP {st.hp if st else '?'} M {st.mp if st else '?'}, прошло {int(time.time() - t0)} с", flush=True)
        if done:
            foes, _ = w.classify()
            if not foes:
                print("ВРАГОВ НЕТ — ласт зачищен", flush=True)
                break
        if st and st.mp < 4000:
            print("мана < 4000", flush=True)
            flee()
            break
        if time.time() - t0 > 420:
            print("7 минут боя — стоп", flush=True)
            break
except SystemExit as e:
    print("СТОП:", e, flush=True)
    flee()
for l in w.answer("задания", 1.5):
    if "Убить" in l or "Выполнить" in l:
        print(l.strip(), flush=True)
