# -*- coding: utf-8 -*-
"""Запуск списка зон надсмотрщиком (аварии -> стоп и сообщение): python tools/run_zones.py зона1 зона2 ..."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S
for z in sys.argv[1:]:
    S.say("ЗАПУСК:", z)
    r = S.run_zone(z)
    if r != "end":
        S.say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: остановка на зоне", z, r); sys.exit(1)
S.say("все зоны списка пройдены:", " ".join(sys.argv[1:]))
