# -*- coding: utf-8 -*-
"""Круг для 21+ (Айлина-лидер + Кимпи): ель, конюшни, переход_р1, луга, переход_р2 ... по кругу. Останов/авария - сообщение и всплывающее окно."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S
CIRCLE = ["храм", "бесы", "геоканал3", "переход_р1", "змеи", "переход_р1", "гномы"]
k = CIRCLE.index(sys.argv[sys.argv.index("--zone") + 1]) if "--zone" in sys.argv else 0
attach = "--attach" in sys.argv
while True:
    z = CIRCLE[k % len(CIRCLE)]; k += 1
    S.say("КРУГ 21+:", z)
    r = S.run_zone(z, attach); attach = False
    if r == "end" and z in ("бесы", "змеи", "гномы"):
        # из бесов (3 этаж) пешком не выйти - как в логе пользователя: охранный свиток руками обеим, потом круг сам дойдёт до старта следующей зоны
        import walker as _w
        if z == "бесы":
            S.jmc("зач охр")            # в змеях Айлина читает свиток сама (последняя строка маршрута Чвырлы)
        _w.Jaba("JMC БОТ ИНКА").send("зач охр", 1.0); import time as _t; _t.sleep(8); S.say("бесы: вышли охранным свитком")
    if r == "restart":
        k -= 1; continue
    if r != "end":
        S.alert_user("Круг остановлен на зоне %s (%s). Смотри лог надсмотрщика." % (z, r))
        S.say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: круг 21+ остановлен на", z, r); sys.exit(1)
