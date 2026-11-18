# -*- coding: utf-8 -*-
"""Три проверяемых скрипта для пары Айлина (лидер) + Кимпи (компаньон). Каждый возвращает (ok, причина) и ничего не делает «на авось».
  1. group_ok()          - проверка группы: «группа» показывает обоих? Добавляет Кимпи ТОЛЬКО если её нет (команда «группа <имя>» - переключатель: если уже в группе, ИСКЛЮЧАЕТ).
  2. area_state()        - таблицы «обл» у обоих; area_visitor_ok(имя) - зона в таблице у ОБОИХ (Кимпи в таблице = посетитель инста).
  3. where() / go(...)   - клетка (MSDP) каждой; перемещение по графу game.db пачками (walker.walk) или назад по маршруту зоны (back_by_route).
python tools/mad_ctl.py status   - только чтение: где обе, состав группы, таблицы областей."""
import os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import walker
from walker import Jaba
LEAD, COMP = "JMC БОТ АЙЛИНА", "JMC БОТ ИНКА"
COMP_NAME = "Кимп"
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}


def _ask(j, cmd, wait=3.0):
    """Послать команду и вернуть текст, который появился в логе жабы."""
    pos = os.path.getsize(j.log); j.send(cmd, 1.0); time.sleep(wait)
    return j.tail(pos)


# ---------- 1. группа ----------
def group_members():
    t = _ask(Jaba(LEAD), "группа")
    names = []
    for s in t.splitlines():
        m = re.match(r"^(?:\d\d:\d\d:\d\d )?\s+([А-Яа-яЁё\-]+)\s+#+\s+#+\s+#+\s+(\S+)\s+([ДН])\b", s)
        if m:
            names.append((m.group(1), m.group(3) == "Д"))      # (имя, «Рядом»)
    return names


def group_ok(add=True):
    """(ok, текст). ok = Кимпи в группе. Добавляет, только если её нет в списке."""
    mem = group_members()
    if any(n.lower().startswith(COMP_NAME.lower()) for n, _ in mem):
        return True, "в группе: " + ", ".join("%s(%s)" % (n, "рядом" if near else "не рядом") for n, near in mem)
    if not add:
        return False, "Кимпи нет в группе: %s" % mem
    t = _ask(Jaba(LEAD), "группа " + COMP_NAME, 3)
    mem = group_members()
    ok = any(n.lower().startswith(COMP_NAME.lower()) for n, _ in mem)
    return ok, ("добавила: " if ok else "НЕ добавилась: ") + ", ".join(n for n, _ in mem) + " | ответ: " + " ".join(t.split())[:80]


# ---------- 2. область ----------
def area_state(folder):
    """Таблица «обл» персонажа: список (номер, название, лидер, репоп, таймер-текст)."""
    t = _ask(Jaba(folder), "обл", 3)
    rows = []
    for s in t.splitlines():
        m = re.match(r"^(?:\d\d:\d\d:\d\d )?\s*(активен|удален\S*|\S+)\s+(\d+)\s+(.+?)\s{2,}(\S+)\s+(\d+)\s+(.+)$", s)
        if m and m.group(1).startswith("активен"):
            rows.append((m.group(2), m.group(3).strip(), m.group(4), m.group(5), m.group(6).strip()))
    return rows


def area_visitor_ok(area_name):
    """True, если инст этой зоны есть в таблице у ОБОИХ: значит Кимпи - посетитель (иначе в инст ей не попасть никогда)."""
    a = [r for r in area_state(LEAD) if area_name.lower() in r[1].lower()]
    k = [r for r in area_state(COMP) if area_name.lower() in r[1].lower()]
    return bool(a) and bool(k), "Айлина: %s | Кимпи: %s" % (a or "нет", k or "нет")


# ---------- 3. перемещение ----------
def where():
    return Jaba(LEAD).vnum(), Jaba(COMP).vnum()


def go(folder, dst):
    """По графу game.db пачками, со сверкой клетки. Клетки вне графа (инсты, лес) - только back_by_route."""
    return walker.walk(folder, dst, say=print)


def back_by_route(folder, zone):
    """Назад по маршруту зоны (areas/<зона>.botp Айлины): ходы от начала до текущей клетки в обратном порядке, пачками по 10 с проверкой клетки."""
    L = open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "JMC БОТ АЙЛИНА", "areas", zone + ".botp"), "rb").read().decode("cp1251").splitlines()
    J = Jaba(folder); cur = J.vnum()
    idx = next((i for i, ln in enumerate(L) if "== %s}" % cur in ln), None)
    if idx is None:
        return False, "клетки %s нет в маршруте %s" % (cur, zone)
    mv = []
    for ln in L[1:idx]:
        m = re.search(r"== \d+\} \{([^}]*)\}", ln)
        if m:
            mv += [c.strip() for c in m.group(1).split(";") if c.strip() in OPP]
    rev = [OPP[c] for c in reversed(mv)]
    for i in range(0, len(rev), 10):
        J.send(";".join(rev[i:i + 10]), 1.0); time.sleep(0.9 * len(rev[i:i + 10]) + 2)
    return True, "прошла %d ходов, клетка %s" % (len(rev), J.vnum())


def catch_up_by_log(max_lines=20000):
    """Подвести Кимпи к Айлине там, где клеток нет в графе (новые зоны): по логу бота Айлины берём шаги «## STEP n vn=X cmd=...»
    от последнего шага в клетке, где стоит Кимпи, до текущего и повторяем ходы Кимпи. (ok, текст)"""
    a, k = Jaba(LEAD), Jaba(COMP)
    av, kv = a.vnum(), k.vnum()
    if av == kv:
        return True, "уже рядом " + str(av)
    L = open(a.log, "rb").read()[-6_000_000:].decode("cp1251", "replace").splitlines()[-max_lines:]
    steps = []
    for s in L:
        m = re.search(r"## STEP \d+ vn=(\d+) cmd=(.*)$", s)
        if m:
            cmd = m.group(2)
            mm = re.search(r"== \d+\} \{([^}]*)\}", cmd)
            body = mm.group(1) if mm else cmd
            steps.append((m.group(1), [c.strip() for c in body.split(";") if c.strip() in OPP or c.strip().startswith(("откр", "отпер"))]))
    idx = max((i for i, (v, _) in enumerate(steps) if v == kv), default=None)
    if idx is None:
        return False, "клетки Кимпи %s нет в пройденном пути Айлины" % kv
    cmds = [c for _, cs in steps[idx:] for c in cs]
    for i in range(0, len(cmds), 8):
        k.send(";".join(cmds[i:i + 8]), 1.0); time.sleep(0.9 * len(cmds[i:i + 8]) + 1.5)
    nv = k.vnum()
    return nv == a.vnum(), "Кимпи %s -> %s (Айлина %s), ходов %d" % (kv, nv, a.vnum(), len(cmds))


def resume(zone, step):
    """Продолжить зону в жабе Айлины с шага step (номер строки botp с 0, как «## STEP N» в логе)."""
    a = Jaba(LEAD)
    for c in ("#scr botCore.enableBot = false", "#scr botCore.loadZone('%s')" % zone, "#scr botCore.waitFlag = false",
              "#scr seekstep = %d" % step, "#scr botCore.BotInZone = true", "#scr botCore.enableBot = true", "look краткий"):
        a.send(c, 0.6); time.sleep(0.6)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "catchup":
        print(catch_up_by_log())
    if len(sys.argv) > 3 and sys.argv[1] == "resume":
        print("клетки", where(), group_ok(add=False)); resume(sys.argv[2], int(sys.argv[3])); print("продолжено", sys.argv[2], "с шага", sys.argv[3])
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        a, k = where()
        print("клетки: Айлина", a, "| Кимпи", k)
        print("группа:", group_ok(add=False))
        for nm, f in (("Айлина", LEAD), ("Кимпи", COMP)):
            print("области", nm + ":", area_state(f))
