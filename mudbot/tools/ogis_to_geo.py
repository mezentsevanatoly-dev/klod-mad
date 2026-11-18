"""Огис (из зоны лечебницы или города) -> Повозки Огиса (180154) -> `ехать гео` -> Склад Геоланта (115092)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto as g  # noqa: E402
from botp_walk import Walker  # noqa: E402
from to_geo import wait_room  # noqa: E402

w = Walker({})
w.last_msdp_from_log()
if w.cur["area"] != "Город Геолант":
    if w.cur["vnum"] != "180154" and not g.goto(w, "180154"):
        sys.exit("не дошли до повозок Огиса")
    w.pump(1)
    w.c.send("ехать гео")
    print("едем в Геолант", flush=True)
    if not wait_room(w, lambda c: c["area"] == "Город Геолант" and c["name"] != "Тарантас", 300):
        sys.exit(f"не доехали: {w.cur['area']} | {w.cur['name']}")
    w.pump(2)
if w.cur["vnum"] != "115092" and not g.goto(w, "115092"):
    sys.exit("не дошли до Склада Геоланта")
print("на Складе Геоланта", flush=True)
