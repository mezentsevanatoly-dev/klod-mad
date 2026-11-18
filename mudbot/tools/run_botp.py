"""Пройти .botp от текущей комнаты (область уже создана, без дороги и создания): python tools/run_botp.py <файл.botp> [с_шага] [до_шага]

Нужен для кусков квеста по сценарию (tools/quest_route.py): между кусками проверяем `задания`. Мобов Чвырлы берём из пустого csv.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import botp_walk as b  # noqa: E402

empty = os.path.join(os.path.dirname(HERE), "areas", "routes", "_empty_mob.csv")
if not os.path.exists(empty):
    open(empty, "w", encoding="cp1251").write("Описание в комнате;Имя моба;Уровень;Флаги NPC\n")
botp = sys.argv[1]
sys.argv = [sys.argv[0], botp, empty] + sys.argv[2:]
b.main()
