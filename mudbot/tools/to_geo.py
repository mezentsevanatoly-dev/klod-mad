"""Поездка в Геолант: Склад Элендора -> `путь кон` -> `ехать гео` (повозка) -> Склад Геоланта (115092).

python tools/to_geo.py   (из любой точки Элендора; обратно: tools/to_elendor.py пока нет)
Конюшни экономят мувы: пешком до Геоланта не ходим (польз.). Повозка едет ~минуту, ждём по MSDP.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto as g  # noqa: E402
from botp_walk import Walker  # noqa: E402

GEO_STORE = "115092"


def wait_room(w, ok, secs):
    t0 = time.time()
    while time.time() - t0 < secs:
        w.pump(0.5)
        w.last_msdp_from_log()
        if ok(w.cur):
            return True
    return False


def main():
    w = Walker({})
    w.last_msdp_from_log()
    if w.cur["area"] == "Город Геолант":
        print("уже в Геоланте", flush=True)
    else:
        if not w.cur["area"].startswith("Город Элендор"):
            sys.exit(f"не в Элендоре ({w.cur['area']}): сначала выйти в город")
        w.c.send("путь кон")
        if not wait_room(w, lambda c: c["name"] == "Конюшня", 90):
            sys.exit(f"не дошли до конюшни: {w.cur['name']}")
        w.pump(1)
        w.c.send("ехать гео")
        print("едем в Геолант", flush=True)
        if not wait_room(w, lambda c: c["area"] == "Город Геолант", 240):
            sys.exit(f"не доехали: {w.cur['area']} | {w.cur['name']}")
        w.pump(2)
    print(f"в Геоланте: {w.cur['vnum']} {w.cur['name']}; иду на Склад", flush=True)
    if w.cur["vnum"] != GEO_STORE and not g.goto(w, GEO_STORE):
        sys.exit("не дошли до Склада Геоланта")
    print("на Складе Геоланта", flush=True)


if __name__ == "__main__":
    main()
