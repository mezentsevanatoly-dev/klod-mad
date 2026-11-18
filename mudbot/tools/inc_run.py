"""Этапы прокачки по логам пользователя: python tools/inc_run.py <лог> <стоп_уровень> [--noentry]

Вход: шаги лога до `область создать …` (дорога, гильдия, покупки — без боёв) + первый шаг в зону, потом охота по миникарте
(MapHunter.run): бьём всех в клетке, идём к ближайшей клетке с m/M, зона пройдена или уровень достигнут — стоп.
Старт — Склад Элендора (100076) или клетка, где уже стоим при --here.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_db import DB  # noqa: E402
from hunt_luga import LevelReached  # noqa: E402
from mapfight import MapHunter  # noqa: E402
from replay import Replay  # noqa: E402


def main():
    name, stop = sys.argv[1], int(sys.argv[2])
    steps = json.load(open(os.path.join(DB, "routes", name + ".json"), encoding="utf-8"))["steps"]
    h = Replay(stop)
    from mapfight import allowed
    h.allow, h._names, h.strict = allowed([name]), None, True      # мобы только из лога этого этапа
    if "--all" in sys.argv:                                         # школа (польз. 07.11: «мобов пропускал»): бить всех, кроме учителя, без осмотра
        h.strict, h.kill_all, h.fast_all, h.below, h.skip_below = False, True, True, 99, 0
    h.sync_level()
    h.last_msdp_from_log()
    idx = next((i for i, s in enumerate(steps) if "cmd" in s and s["cmd"].startswith("область создать")), None)
    if "--here" not in sys.argv:
        h.goto_home()
    if idx is None and "--noentry" not in sys.argv:     # нет команды создания области (зона открытая): входим по шагам лога до первого боя
        first_kill = next((i for i, s in enumerate(steps) if "kill" in s), len(steps))
        print(f"{name}: открытая зона, вход {first_kill} шагов до первого боя, уровень {h.level}", flush=True)
        h.walk_steps([s for s in steps[:first_kill] if "kill" not in s], True)
        if h.cur["area"].startswith("Город Элендор"):
            sys.exit("после входа всё ещё в Элендоре: стоп (в городе не бью)")
    if idx is not None and "--noentry" not in sys.argv:
        print(f"{name}: вход {idx + 1} шагов до «{steps[idx]['cmd']}», уровень {h.level}", flush=True)
        first = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0     # продолжить вход с шага N (уже проехали)
        entry = [s for s in steps[first:idx + 1] if "kill" not in s]
        nxt = next((s for s in steps[idx + 1:] if "move" in s or "kill" in s), None)     # между созданием и входом может стоять справка `обл`
        if nxt and "move" in nxt:
            entry.append(nxt)                   # первый шаг в зону — после создания (направление создания берётся из него)
            idx = steps.index(nxt) - 1
        h.walk_steps(entry, True)
    entry_vnum, create_cmd, first_move = None, None, None
    if idx is not None:
        create_cmd = steps[idx]["cmd"]
        first_move = steps[idx + 1]["move"] if idx + 1 < len(steps) and "move" in steps[idx + 1] else None
    t0 = time.time()
    if "--seq" in sys.argv and idx is not None:           # убийства в том же порядке, что в логе пользователя, с фильтром по опыту
        h.zone = h.cur["area"]
        rest = [s for s in steps[idx + 2:] if "cmd" not in s]
        print(f"порядок лога: {len(rest)} шагов в зоне «{h.zone}», уровень {h.level}", flush=True)
        try:
            if h.walk_steps(rest):
                print(f"ДОСТИГНУТ {h.level} УРОВЕНЬ", flush=True)
                print(f"за {int(time.time() - t0) // 60} мин: убито {h.total['kills']}, опыт {h.total['xp']}, монет {h.total['gold']}", flush=True)
                return
        except SystemExit as e:
            if str(e.code).startswith("ПЕРСОНАЖ ПОГИБ"):
                raise
            print(f"сбились с порядка лога ({e.code}); дальше охота по карте", flush=True)
    for rnd in range(1, 8):                     # зона зачищена, а уровня нет: удалить экземпляр и создать заново (как делает пользователь)
        if rnd == 1:
            h.zone = h.cur["area"]                # зона этапа запоминается один раз; дальше только проверяем, что вошли в неё
        elif h.cur["area"] != h.zone:
            print(f"после пересоздания мы в «{h.cur['area']}», а не в «{h.zone}»: стоп (в чужой зоне не бью)", flush=True)
            break
        start_v = h.cur["vnum"]
        h.pos, h.skip, h.visited, h.graph, h.bad, h.outside = (0, 0, 0), set(), set(), {}, set(), set()
        print(f"охота в зоне «{h.zone}» до {stop} уровня (заход {rnd})", flush=True)
        try:
            res = MapHunter.run(h)
        except LevelReached:
            print(f"ДОСТИГНУТ {h.level} УРОВЕНЬ", flush=True)
            break
        break                                    # один заход в зону: создал, убил, вышел и пошёл дальше (польз. 02.11), без ожидания и пересоздания
    print(f"за {int(time.time() - t0) // 60} мин: убито {h.total['kills']}, опыт {h.total['xp']}, монет {h.total['gold']}", flush=True)
    from milestones import pending                    # вехи по уровням: что ещё не сделано (гильдия, КСК, биржа)
    for lv, key, text in pending(h.level):
        print(f"ВЕХА [{lv}:{key}] {text}", flush=True)


if __name__ == "__main__":
    main()


