"""Бой в текущей клетке до победы (ласты, группа с Зороном): fight_here по кругу, отступление `вниз`/`убежать` при HP < 40%.

python tools/fight_room.py <mob.csv> [секунд_макс] [направление_отхода]
boss_fight=True: полиморф на лекарей разрешён.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import botp_walk as b  # noqa: E402

w = b.Walker(b.load_mobs(sys.argv[1]))
w.boss_fight = True
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 420
w.last_msdp_from_log()
t0 = time.time()
try:
    for rnd in range(60):
        done = w.fight_here()
        st = w.bot.status
        print(f"раунд {rnd}: HP {st.hp if st else '?'} M {st.mp if st else '?'}, {int(time.time() - t0)} с", flush=True)
        foes, _ = w.classify()
        if done and not foes:
            print("ВРАГОВ НЕТ — зачищено", flush=True)
            break
        if st and st.mp < 3500:
            print("мана < 3500", flush=True)
            raise SystemExit("мана")
        if time.time() - t0 > limit:
            print("лимит времени", flush=True)
            break
except SystemExit as e:
    print("СТОП:", e, flush=True)
    for _ in range(4):
        for c in ("очистить", "вст", "убежать"):
            w.c.send(c)
        w.pump(2.5)
    print("отступила:", w.cur["vnum"], w.cur["name"], flush=True)
for l in w.answer("задания", 1.5):
    if "Убить" in l or "Выполнить" in l:
        print(l.strip(), flush=True)
