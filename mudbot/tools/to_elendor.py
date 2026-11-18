"""Поездка обратно: Геолант -> конюшня Геоланта (115061) -> `ехать 1` (Элендор) -> Склад Элендора (100076).

python tools/to_elendor.py   (из любой точки Геоланта или зоны рядом)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto as g  # noqa: E402
from botp_walk import Walker  # noqa: E402
from to_geo import wait_room  # noqa: E402

STABLE, HOME = "115061", "100076"


def main():
    w = Walker({})
    w.last_msdp_from_log()
    if not w.cur["area"].startswith("Город Элендор"):
        if w.cur["vnum"] != STABLE and not g.goto(w, STABLE):
            sys.exit("не дошли до конюшни Геоланта")
        w.pump(1)
        out = " ".join(w.answer("список", 2)) if hasattr(w, "answer") else ""
        print(out[:300], flush=True)
        w.c.send("ехать 1")
        print("едем в Элендор", flush=True)
        if not wait_room(w, lambda c: c["area"].startswith("Город Элендор"), 240):
            sys.exit(f"не доехали: {w.cur['area']} | {w.cur['name']}")
        w.pump(2)
    if w.cur["vnum"] != HOME and not g.goto(w, HOME):
        sys.exit("не дошли до Склада Элендора")
    print("на Складе Элендора", flush=True)


if __name__ == "__main__":
    main()
