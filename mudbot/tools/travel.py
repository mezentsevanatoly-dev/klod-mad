"""Алиас переезда между городами через Аватару (польз.): `python tools/travel.py <город>`; в cmd.py: `!tp <город>`.

Стоим у Аватары (клетка 90001 «Веранда», где пишем `куп 2`), вся группа рядом. Тогда:
  проверка группы (отстающих призываем сами) -> `сня 10000; куп 2` -> на Перекрёстке `путь портал в <город>`
  -> `войти портал` -> `где`: убеждаемся, что мы в нужном городе. Дальше — спидволки из speedwalks.txt.
Города: гео, ривен, гален, элен, фел, огис, арт, шиар, стэд, видр, эрдер, турнир (или полное имя из `путь список`).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore_msdp import Explorer  # noqa: E402

CITIES = {"гео": "геолант", "ривен": "ривенделл", "гален": "гален", "элен": "элендор", "фел": "фелонад",
          "огис": "огис", "арт": "артуанель", "шиар": "шиар", "стэд": "стэдвик", "видр": "видрир",
          "эрдер": "эрдер", "турнир": "турнирный городок"}
AREAS = {"геолант": "Геолант", "ривенделл": "Ривенделл", "гален": "Гален", "элендор": "Элендор", "фелонад": "Фелонад",
         "огис": "Огис", "артуанель": "Артуанель", "шиар": "Шиар", "стэдвик": "Стэдвик", "видрир": "Видрир",
         "эрдер": "Эрдер", "турнирный городок": "турнир"}


def say(*a):
    print(*a, flush=True)


def group_far(ex):
    """Имена согруппников, у которых в столбце «Рядом» стоит Н (после `груп номер …` строки с номером)."""
    out = ex.answer("пгр позиц ряд", 1.5)
    head = next((l.split()[1:] for l in out if l.strip().startswith("Имя")), [])
    far = []
    ex._members = set()
    for l in out:
        p = l.split()
        if p and p[0].isdigit():
            p = p[1:]
        if head and "Рядом" in head and len(p) == len(head) + 1 and p[0] != "Имя" and not p[0].startswith("-"):
            ex._members.add(p[0].lower())
            if p[1 + head.index("Рядом")] == "Н":
                far.append(p[0])
    return far


def gather(ex, tries=3):
    """Собрать группу в клетке рядом с Аватарой (в клетке самой Аватары `!магия` — призыв не работает, польз.).
    Сначала `к призыв <имя>`; кого не вышло (у Кейба нет доверия на Тадию) — просим группу: `гг !к призыв <имя>`."""
    far = []
    for _ in range(tries):
        far = group_far(ex)
        if not far:
            return []
        for n in far:
            ex.c.send(f"к призыв {n.lower()}")
        for _ in range(3):                                  # ждём не фиксированную паузу, а прихода (опрос каждую секунду)
            ex.pump(1)
            far = group_far(ex)
            if not far:
                return []
        if "карис" in ex._members and "карис" not in [n.lower() for n in far]:
            ex.c.send("гг !очистить")                       # польз.: Карис в группе — призыв через неё
            ex.c.send("гг !сумм")
        else:
            for n in far:
                ex.c.send(f"гг !к призыв {n.lower()}")
        for _ in range(6):
            ex.pump(1)
            if not group_far(ex):
                return []
    return group_far(ex)


def main(name, force=False):
    city = CITIES.get(name.lower(), name.lower())
    ex = Explorer()
    ex.last_msdp_from_log()
    if ex.cur["name"] == "Портал в пустоту":               # клетка рядом с Аватарой: собрать группу здесь, потом в портал
        left = gather(ex)
        if left and not force:
            say("СТОП: не собрались: " + ", ".join(left))
            return False
        ex.answer("войти портал", 5)
        ex.last_msdp_from_log()
    if str(ex.cur["vnum"]) != "90001":
        say(f"СТОП: нужно стоять у Аватары (90001 Веранда), сейчас {ex.cur['vnum']} {ex.cur['name']}")
        return False
    for attempt in range(3):                       # группа рядом (польз.): отстающих призываем сами
        out = ex.answer("пгр позиц ряд", 1.5)
        head = next((l.split()[1:] for l in out if l.strip().startswith("Имя")), [])
        far = []
        for l in out:
            p = l.split()
            if p and p[0].isdigit():                       # после `груп номер …` строки начинаются с номера
                p = p[1:]
            if head and "Рядом" in head and len(p) == len(head) + 1 and p[0] != "Имя" and not p[0].startswith("-"):
                if p[1 + head.index("Рядом")] == "Н":
                    far.append(p[0])
        if not far or force:                               # force: идём с теми, кто рядом (остальных ищем и призываем потом)
            if far:
                say("не рядом (идём без них): " + ", ".join(far))
            break
        for n in far:
            say(f"{n} не рядом — к призыв {n.lower()}")
            ex.answer(f"к призыв {n.lower()}", 2)
    else:
        say("СТОП: группа не собралась")
        return False
    ex.answer("сня 10000", 1.5)
    ex.move_cmd("куп 2", 8)                         # перенос группы на Перекрёсток
    for _ in range(6):
        out = ex.answer_until(f"путь портал в {city}", "достигли пункта назначения|уже находитесь в этой комнате", 30)
        if any("достигли пункта назначения" in l or "уже находитесь в этой комнате" in l for l in out):
            break
        time.sleep(0.5)
    else:
        say("СТОП: не дошла до портала")
        return False
    ex.move_cmd("войти портал", 6)
    where = ex.answer("где", 2)
    say("\n".join(l for l in where if l.strip())[-600:])
    say(f"сейчас: {ex.cur['vnum']} {ex.cur['area']} | {ex.cur['name']}")
    area = AREAS.get(city, city)
    ok = area.lower() in ex.cur["area"].lower()
    say("на месте" if ok else "ВНИМАНИЕ: зона не совпала, проверьте `где`")
    return ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    sys.exit(0 if main(" ".join(args), "--force" in sys.argv) else 1)
