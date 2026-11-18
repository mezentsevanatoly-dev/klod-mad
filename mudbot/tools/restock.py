# -*- coding: utf-8 -*-
"""Расходники (слова пользователя 02.11 и 13.11: носить минимум по 2 экземпляра каждого, камней 1; у расходников есть заряды, поэтому по 2).
На складе: `инв` -> экземпляры по типам; не хватает - `кз :колбы <слово>` по одному; в :колбы нет - в список «докупить» (алхимик: охранный 5000, камни 20000,
панацея 10000, мыши 5000, прозрение 4186; номера в `спис` Геоланта: 2 охр, 4 камни, 5 панац, 9 мыши, 11 прозр). python tools/restock.py <папка жабы> [--buy]"""
import os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from walker import Jaba, walk
NEED = {"мыши": ("мыш", 2), "охранный свиток": ("охран", 2), "панацея": ("панац", 2), "камни": ("камн", 1),
        "восстановление": ("восст", 2), "насыщение": ("насыщ", 2), "прозрение": ("проз", 2)}
SHOP = {"охранный свиток": "охр", "мыши": "мыш", "прозрение": "прозре", "восстановление": "восс", "насыщение": "насы"}     # слова из твоих логов: куп охр 2, куп мыш 5, куп прозре 5, куп восс 10, куп насы 10
KZ = {"мыши": "мыши", "охранный свиток": "охр", "панацея": "панацея", "камни": "камн", "восстановление": "восст", "насыщение": "насыщ", "прозрение": "прозр"}     # формы из твоих логов: кз :колбы охр / восст / насыщ / мыши / прозр / панацея
STORE = ":колбы"


def counts(j):
    pos = os.path.getsize(j.log); j.send("инв", 2.0)
    t = [re.sub(r"^\d\d:\d\d:\d\d ", "", s) for s in j.tail(pos).splitlines()]
    items = []; on = False
    for s in t:
        if "Вы несете" in s:
            on = True; continue
        if on:
            if re.search(r"\d+H \d+M", s):
                break
            if s.strip():
                m = re.search(r"\[(\d+)\]\s*$", s.strip()); items.append((s.strip(), int(m.group(1)) if m else 1))
    return items


def have(items, kw):
    return sum(n for s, n in items if re.search(kw, s, re.I))


def restock(folder, say=print):
    j = Jaba(folder); items = counts(j); missing = {}
    for name, (kw, need) in NEED.items():
        h = have(items, kw); tries = 0
        while h < need and tries < need + 1:
            pos = os.path.getsize(j.log); j.send("кз %s %s" % (STORE, KZ[name]), 1.8)
            if "нет '" in j.tail(pos) and "забрали" not in j.tail(pos):
                break
            tries += 1; items = counts(j); h = have(items, kw)
        if h < need:
            missing[name] = need - h
        say("   %-16s %d из %d%s" % (name, h, need, "" if h >= need else "  -> ДОКУПИТЬ %d" % (need - h)))
    return missing


WANT = {"охранный свиток": r"охранный свиток", "камни": r"заклинателя камней", "панацея": r"панацеи", "мыши": r"летучей мыши\s*$", "прозрение": r"эликсир прозрения"}


SOURCE = {"охранный свиток": "алхимик", "панацея": "алхимик", "камни": "алхимик", "мыши": "алхимик",
          "насыщение": "шатёр", "восстановление": "шатёр", "прозрение": "эрдер", "солнце": "колбы (уже куплено пользователем)"}


def erder_trip(folder, n, say=print):
    """Прозрение: Эрдер, «Башня алхимика» (колба прозрения 1000). Маршрут из твоего скрипта заточки: путь аватар; клан снять 333333; куп 1; путь эрдер; войти; путь алхим; спис; куп №;
    обратно: путь аватар; куп 1; путь элен|гео; войти; путь склад. Ворота по дороге открывают твои триггеры."""
    j = Jaba(folder); home = j.vnum() or ""; back = "путь элен" if home.startswith("100") else "путь гео"
    for c, w in (("путь аватар", 9), ("клан снять 333333", 2), ("куп 1", 3), ("путь эрдер", 9), ("войти", 4), ("путь алхим", 9)):
        j.send(c, w)
    pos = os.path.getsize(j.log); j.send("спис", 2.5)
    lst = {}
    for s in j.tail(pos).splitlines():
        m = re.match(r"^\d\d:\d\d:\d\d\s+(\d+)\.\s*\[\s*(\d+)\]\s*(.+?)\s*$", s)
        if m:
            lst[int(m.group(1))] = m.group(3)
    num = next((k for k, v in lst.items() if re.search(r"прозрения", v, re.I)), None)
    if num:
        j.send("куп %d %d" % (num, n), 3.0); say("   Эрдер: куплено прозрение x%d (№%d %s)" % (n, num, lst[num]))
    else:
        say("   Эрдер: прозрения в списке алхимика нет")
    for c, w in (("путь аватар", 9), ("куп 1", 3), (back, 9), ("войти", 4), ("путь склад", 9)):
        j.send(c, w)


def buy(folder, missing, say=print, run_zone=None):
    """Решение «КСК или купить» (слова пользователя 13.11): в :колбы нет -> покупаю там, где продаётся:
    алхимик (путь алхим, спис, куп №): охранный, панацея, камни, мыши; шатёр: скрипт-зона закупка_насыщ (настойки насыщения/восстановления);
    прозрение - Эрдер; солнца - магазин путешествий в Элендоре (эти две поездки пока не автоматизированы - говорю прямо)."""
    j = Jaba(folder)
    alch = {k: v for k, v in missing.items() if SOURCE.get(k) == "алхимик"}
    if alch:
        j.send("путь алхим", 9.0)
        pos = os.path.getsize(j.log); j.send("спис", 2.5)
        lst = {}
        for s in j.tail(pos).splitlines():
            m = re.match(r"^\d\d:\d\d:\d\d\s+(\d+)\.\s*\[\s*(\d+)\]\s*(.+?)\s*$", s)
            if m:
                lst[int(m.group(1))] = m.group(3)
        for name, n in alch.items():
            num = next((k for k, v in lst.items() if name in WANT and re.search(WANT[name], v, re.I)), None)
            if num:
                j.send("куп %d %d" % (num, n), 3.0); say("   куплено %s x%d (алхимик №%d %s)" % (name, n, num, lst[num]))
            else:
                say("   %s: в списке алхимика нет" % name)
        j.send("путь склад", 9.0)
    if any(SOURCE.get(k) == "шатёр" for k in missing):
        if run_zone:
            say("   настойки: иду в Шатёр (скрипт закупка_насыщ)"); run_zone("закупка_насыщ")
        else:
            say("   настойки: нужен скрипт закупка_насыщ (Шатёр)")
    if missing.get("прозрение", 0) >= 2:      # поездка в Эрдер только если прозрений нет совсем (1 из 2 - ещё хватает, не гонять Кимпи через Аватару)
        erder_trip(folder, missing["прозрение"], say=say)

if __name__ == "__main__":
    m = restock(sys.argv[1]); print("докупить:", m)
    if m and "--buy" in sys.argv:
        buy(sys.argv[1], m)
