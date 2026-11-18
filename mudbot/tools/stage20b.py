# -*- coding: utf-8 -*-
"""Этап 20 лвл: переход_р1 -> заточка_перчатки (сет3 уже надет). Через функции inc_supervisor (аварии -> стоп и сообщение)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S

for z in ["заточка_перчатки"]:
    S.say("ЭТАП 20: зона", z)
    r = S.run_zone(z, attach=True)
    if r != "end":
        S.say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: этап 20 остановлен на", z, r); sys.exit(1)
S.say("ЭТАП 20: заточка перчаток выполнена (таймер 8 ч). Дальше: гильда Эрдера, дощечка ярости, эликсиры прозрения")