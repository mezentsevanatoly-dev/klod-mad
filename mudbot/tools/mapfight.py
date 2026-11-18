"""Охота по миникарте (как у пользователя): бежим к ближайшей клетке с буквой m/M на карте и бьём, кто там есть.

python tools/mapfight.py <стоп_уровень> [--route имя_лога ...] [--extra N] [--skip N] [--all]
  Стоим в нужной зоне (на входе или в любой её клетке). Режим карты — `реж карта сверху` (7x7, мы в центре).
  1. В клетке: бьём мобов по строкам комнаты (BarbHunter.pick/fight_here); «разрешённые» имена — из логов пользователя
     (--route парк аллея …: все имена из data/db/routes/<лог>.json), для них осмотр не нужен («увидел — убил»);
     незнакомых один раз осматриваем `смотреть` (запись в data/db/mobs.csv) и бьём, если уровень <= свой + extra.
  2. Нет мобов в клетке: ближайшая клетка с m/M на миникарте (проходы между клетками читаем с карты).
  3. Мобов на карте нет: ближайшая непосещённая клетка по MSDP-выходам. Всё посещено — зона пройдена.
Клетки, где m/M есть, а бить некого (слишком сильный, мирный), запоминаем (по смещению от входа) и больше туда не ходим.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_db import DB  # noqa: E402
from explore_msdp import BACK, CMD  # noqa: E402
from hunt_luga import BarbHunter, LevelReached  # noqa: E402

VEC = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


class MapHunter(BarbHunter):
    def __init__(self, stop, extra=1, allow=()):
        super().__init__(stop, extra)
        self.allow = {a.lower() for a in allow}
        self.below = 3
        self.strict = False                # True: бить только имена из self.allow (лог этапа)
        self.zone = None
        self.pos = (0, 0, 0)
        self.skip = set()                  # клетки (x, y, z) с m/M, где бить некого
        self.visited = set()
        self.graph = {}                    # vnum -> {dir: vnum}
        self.outside = set()               # vnum чужих зон
        self.area = None

    # ---- цели: имена из логов пользователя разрешены без осмотра
    def known_names(self):
        if getattr(self, "_names", None) is None or len(self.mobs) != getattr(self, "_names_n", -1):
            names = {n: {"name": n, "level": "", "flags": "", "skills": ""} for n in self.allow}
            for m in self.mobs.values():
                if m.get("name"):
                    names[m["name"].lower()] = m
            if self.strict:
                names = {k: v for k, v in names.items() if k in self.allow}
            self._names, self._names_n = names, len(self.mobs)
        return self._names

    def target(self, line):
        from hunt_zone import mob_key
        low0 = line.lower()
        if getattr(self, "fast_names", None) and self.THING.search(line):
            return None                                       # труп, портал, доска, учитель: не цель
        for n in getattr(self, "fast_names", ()):             # быстрый режим (польз. 03.11, школа): только имена, без осмотра и проверок уровня
            if n in low0:
                return {"name": n, "look": n, "word": [w for w in n.split() if w not in ("с", "в", "и", "на")][-1],
                        "level": "1", "flags": "", "skills": ""}
        if getattr(self, "fast_all", False):                  # школа (польз. 03.11): без ограничений, бить любого моба, кроме учителя на входе
            if self.THING.search(line):
                return None
            from explore_msdp import mob_words
            for n in sorted(getattr(self, "fast_names", ()), key=len, reverse=True):      # имя из базы -> его слово цели («бабочка», «моль»)
                if re.search(r"(?<![а-яё])" + re.escape(n) + r"(?![а-яё])", line.lower()):
                    return {"name": n, "look": n, "word": [w for w in n.split() if w not in ("с", "в", "и", "на")][-1],
                            "level": "1", "flags": "", "skills": ""}
            ws = mob_words(line)
            return {"name": line.strip()[:40], "look": line.strip(), "word": ws[0], "level": "1", "flags": "", "skills": ""} if ws else None
        m = self.mobs.get(mob_key(line))
        if m and m.get("word") and int(m.get("level") or 0):          # осмотрен ботом: правило по уровню
            if "Мирный" in m.get("flags", "") or int(m["level"]) <= self.skip_below:
                return None
            if self.strict and (m.get("name") or "").lower() not in self.allow:
                return None                      # моб не из лога этого этапа (польз.: в каждом логе свои мобы; людей 15+ на 12 лвл не бьём)
            if not self.kill_all and not (self.level - self.below <= int(m["level"]) <= self.level + self.extra):
                return None                      # бьём, если уровень моба в пределах свой +-3 (польз.)
            if self.low_yield(m.get("name") or m.get("look")) or self.capped(m.get("name") or m.get("look"), int(m.get("level") or 0)):
                return None                      # вид даёт мало (слабый моб или замакс) или ровно потолок (на след. уровне даст больше): оставляем на потом
            return m
        low = line.lower()
        hit = next((n for n in sorted(self.known_names(), key=len, reverse=True) if n in low), None)
        if not hit:
            return None
        m = dict(self.known_names()[hit])
        lv = int(m.get("level") or 0)
        if not lv:
            return None                          # уровень неизвестен: сначала осмотреть (`см`), потом решать
        if lv and not self.kill_all and not (self.level - self.below <= lv <= self.level + self.extra):
            return None                          # имя из логов, но уровень в БД слишком большой (пожилой конюх 25 -> смерть 02.11)
        m["word"] = [w for w in hit.split() if w not in ("с", "в", "и", "на")][-1]
        if self.low_yield(m.get("name") or hit) or self.capped(m.get("name") or hit, lv):
            return None
        return None if "Мирный" in m.get("flags", "") else m

    # ---- миникарта
    def grid(self):
        mm = getattr(self, "minimap", None)
        if not mm or len(mm) < 15:
            return None
        return [l.ljust(29) for l in mm[:15]]

    def cells_with_mobs(self):
        """Клетки миникарты с m/M (кроме своей): [(r, c)]."""
        mm = self.grid()
        if not mm:
            return [], None
        out = []
        for r in range(7):
            for c in range(7):
                if (r, c) != (3, 3) and set("mM") & set(mm[2 * r + 1][4 * c + 1:4 * c + 4]):
                    out.append((r, c))
        return out, mm

    @staticmethod
    def open_edges(mm, r, c):
        res = []
        if r > 0 and mm[2 * r][4 * c + 2] in " ~":
            res.append(("N", r - 1, c))
        if r < 6 and mm[2 * r + 2][4 * c + 2] in " ~":
            res.append(("S", r + 1, c))
        if c > 0 and mm[2 * r + 1][4 * c] in ": ":
            res.append(("W", r, c - 1))
        if c < 6 and mm[2 * r + 1][4 * c + 4] in ": ":
            res.append(("E", r, c + 1))
        return res

    def abs_of(self, r, c):
        return (self.pos[0] + c - 3, self.pos[1] + r - 3, self.pos[2])

    def mob_step(self):
        """Первый шаг к ближайшей клетке с мобом по проходам миникарты, или None."""
        cells, mm = self.cells_with_mobs()
        goals = {rc for rc in cells if self.abs_of(*rc) not in self.skip}
        if not goals:
            return None
        prev, q = {(3, 3): None}, [(3, 3)]
        while q:
            cur = q.pop(0)
            if cur in goals:
                while prev[cur][0] != (3, 3) if prev[cur] else False:
                    cur = prev[cur][0]
                return prev[cur][1] if prev[cur] else None
            for d, r, c in self.open_edges(mm, *cur):
                if (r, c) not in prev and "#" not in mm[2 * r + 1][4 * c + 1:4 * c + 4]:
                    prev[(r, c)] = (cur, d)
                    q.append((r, c))
        return None

    # ---- ходьба
    def step(self, d):
        before = self.cur["vnum"]
        if str(self.cur["exits"].get(d)) in getattr(self, "avoid", ()):       # опасная комната (агрессивный моб выше уровня): не входим
            self.bad.add((before, d))
            return False
        ok = self.move(d) or (self.open_door(d) and self.move(d)) or self.move(d) or self.move(d)   # в темноте оглянуться не видит дверь, но триггер бота уже открыл её
        if not ok:
            self.bad.add((before, d))
            return False
        self.pos = (self.pos[0] + VEC.get(d, (0, 0))[0], self.pos[1] + VEC.get(d, (0, 0))[1],
                    self.pos[2] + (1 if d == "U" else -1 if d == "D" else 0))
        if self.cur["area"] != self.area:                  # вышли за границу зоны: назад
            self.outside.add(self.cur["vnum"])
            self.move(BACK[d])
            self.pos = (self.pos[0] - VEC.get(d, (0, 0))[0], self.pos[1] - VEC.get(d, (0, 0))[1],
                        self.pos[2] - (1 if d == "U" else -1 if d == "D" else 0))
            return False
        self.note_room()
        return True

    def note_room(self):
        v = self.cur["vnum"]
        self.visited.add(v)
        self.graph[v] = {d: str(t) for d, t in self.cur["exits"].items() if d in CMD}

    def frontier_step(self):
        """Первый шаг к ближайшей непосещённой комнате по графу MSDP."""
        v0 = self.cur["vnum"]
        prev, q = {v0: None}, [v0]
        while q:
            v = q.pop(0)
            if v not in self.visited and v != v0 and v not in self.outside:
                while prev[v][0] != v0:
                    v = prev[v][0]
                return prev[v][1]
            for d, t in self.graph.get(v, {}).items():
                if t not in prev and t not in self.outside and (v, d) not in self.bad:
                    prev[t] = (v, d)
                    q.append(t)
        return None

    # ---- главный цикл
    def run(self, max_minutes=600):
        self.last_msdp_from_log()
        if self.zone and self.cur["area"] != self.zone:
            sys.exit(f"мы в зоне «{self.cur[chr(97)+chr(114)+chr(101)+chr(97)]}», а охота — только в «{self.zone}»: стоп")
        self.area = self.cur["area"]
        if self.area.startswith("Город Элендор"):
            sys.exit("мы в городе Элендор: охота здесь запрещена (стоп)")
        self.note_room()
        t_end = time.time() + max_minutes * 60
        idle = 0
        while time.time() < t_end:
            self.wait_alarm()
            k0 = self.total["kills"]
            self._fought = None
            if not self.last_room or self.last_room.name != self.cur["name"]:
                self.look()                                    # описание комнаты ещё не разобрано: обновить
            if time.time() - getattr(self, "_corpse_t", 0) > 90 and any("Труп Ждадиуса" in l for l in self.bot.history[-30:]):
                self._corpse_t = time.time()                                  # свой труп с вещами: забрать и одеть
                self.answer("взять все труп ждадиуса", 2)
                self.answer("од все", 2)
            self.fight_here()
            here_marked = any(set("mM") & set(self.grid()[7][4 * 3 + 1:4 * 3 + 4])) if self.grid() else False
            if here_marked and self.total["kills"] == k0:
                self.look()                                    # метка есть, а не били: вторая попытка по свежему описанию
                self.fight_here()
                here_marked = any(set("mM") & set(self.grid()[7][4 * 3 + 1:4 * 3 + 4])) if self.grid() else False
            if here_marked and self.total["kills"] == k0:
                self.skip.add(self.pos)                      # метка есть, бить некого: больше не приходим
            hist = self.__dict__.setdefault("_hist", [])
            hist.append(self.cur["vnum"])
            del hist[:-10]
            if len(hist) >= 8 and len(set(hist[-8:])) <= 2 and self.total["kills"] == k0:
                self._map_off = 12                              # петля между двумя комнатами (карта показывает мобов за стеной): 12 шагов по графу MSDP
                print(f"петля {sorted(set(hist[-8:]))}: 12 шагов без карты", flush=True)
                hist.clear()
            d = None if getattr(self, "_map_off", 0) > 0 else self.mob_step()
            if getattr(self, "_map_off", 0) > 0:
                self._map_off -= 1
            if d is None:
                d = self.frontier_step()
                if d is None:
                    print(f"зона пройдена: убито {self.total['kills']}, опыт {self.total['xp']}; комнат {len(self.visited)}, "
                          f"чужих {len(self.outside)}, неудачных ходов {sorted(self.bad)[:12]}, пропущено клеток {len(self.skip)}", flush=True)
                    return "cleared"
            if not self.step(d):
                idle += 1
                self.safe()
                if idle > 40:
                    print("застряли: слишком много неудачных шагов", flush=True)
                    return
            else:
                idle = 0
            if self.bot.status and self.bot.status.in_battle:
                self.safe()


def allowed(routes):
    out = set()
    if routes == ["all"]:                      # все имена из всех логов пользователя
        routes = [f[:-5] for f in os.listdir(os.path.join(DB, "routes")) if f.endswith(".json")]
    for r in routes:
        for s in json.load(open(os.path.join(DB, "routes", r + ".json"), encoding="utf-8"))["steps"]:
            for n in s.get("kill", []):
                out.add(n.lower())
    return out


def main():
    argv = sys.argv[1:]
    routes = []
    if "--route" in argv:
        i = argv.index("--route") + 1
        while i < len(argv) and not argv[i].startswith("--"):
            routes.append(argv[i])
            i += 1
    nums = [a for k, a in enumerate(argv) if a.isdigit() and (k == 0 or argv[k - 1] not in ("--extra", "--skip"))]
    stop = int(nums[0]) if nums else 99
    opt = lambda o, d: int(argv[argv.index(o) + 1]) if o in argv else d
    h = MapHunter(stop, opt("--extra", 3), allowed(routes))
    h.below = opt("--below", 3)
    if "--zone" in argv:
        h.zone = argv[argv.index("--zone") + 1]
    h.skip_below = opt("--skip", 0)
    h.kill_all = "--all" in argv
    h.strict = "--strict" in argv                      # бить только имена из логов этапа (города: стражи рядом)
    if "--avoid" in argv:                              # --avoid 226125 [vnum ...]: комнаты, в которые не входим
        i = argv.index("--avoid") + 1
        h.avoid = set()
        while i < len(argv) and argv[i].isdigit():
            h.avoid.add(argv[i])
            i += 1
    h.survey = "--survey" in argv                      # разведка мира: бить всех не выше свой+extra, без фильтров по опыту; карточки и опыт в game.db
    h.never = [x.strip().lower() for x in argv[argv.index("--never") + 1].split(",")] if "--never" in argv else []     # слова строки комнаты, мобов с которыми не бить (квестовые NPC)
    h.guard = [x.strip().lower() for x in argv[argv.index("--guard") + 1].split(",")] if "--guard" in argv else []     # если такой есть в клетке — не бить никого (ассистят)
    h.once = "--once" in argv
    if h.once and getattr(h, "zone", None):                  # «по одному на имя» держится и между запусками: уже убитые в этой зоне имена берём из game.db
        import sqlite3 as _sq
        _db = _sq.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "game.db"))
        h.killed_names = {r[0].lower() for r in _db.execute("select name from mob_kills where zone=?", (h.zone,)) if r[0]}
        _db.close()
        print(f"уже убиты в зоне (из базы): {len(h.killed_names)}", flush=True)                        # разведка «по разу»: каждый вид убить один раз после осмотра (польз. 03.11)
    h.fast_all = "--fast-all" in argv                # школа: бить любых мобов, кроме учителя (без осмотра и без правил по уровню)
    if "--fast-zone" in argv or (h.fast_all and h.zone):          # имена мобов зоны из базы (mob_zone, role='бить'): бить без осмотра
        import sqlite3
        zname = argv[argv.index("--fast-zone") + 1] if "--fast-zone" in argv else h.zone
        db = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "game.db"))
        h.fast_names = {r[0].lower() for r in db.execute("SELECT name FROM mob_zone WHERE zone=? AND role='бить'", (zname,))}
        db.close()
        print(f"быстрый режим: {len(h.fast_names)} имён без осмотра: {sorted(h.fast_names)}", flush=True)
    h.sync_level()
    print(f"уровень {h.level}, стоп на {stop}, разрешено имён из логов: {len(h.allow)}", flush=True)
    t0 = time.time()
    try:
        h.run()
    except LevelReached:
        print(f"ДОСТИГНУТ {h.level} УРОВЕНЬ", flush=True)
    print(f"за {int(time.time() - t0) // 60} мин: убито {h.total['kills']}, опыт {h.total['xp']}, монет {h.total['gold']}", flush=True)
    from milestones import pending                    # вехи по уровням: что ещё не сделано (гильдия, КСК, биржа)
    for lv, key, text in pending(h.level):
        print(f"ВЕХА [{lv}:{key}] {text}", flush=True)


if __name__ == "__main__":
    main()






