"""Выйти из зоны на Склад Геоланта и пройти этап: python tools/stage.py <лог> <стоп_уровень>   (один заход в зону)"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto as g  # noqa: E402
from botp_walk import Walker  # noqa: E402

w = Walker({})
w.last_msdp_from_log()
if w.cur["vnum"] != "115092":
    print("на Склад Геоланта:", g.goto(w, "115092"), flush=True)
sys.exit(subprocess.call([sys.executable, "-u", "-X", "utf8", os.path.join(HERE, "inc_run.py"), sys.argv[1], sys.argv[2], "--here"]))
