"""Варвар Эсхирд: дойти до Заливных лугов, составить карту по MSDP и бить мобов (до уровня+1), пока не будет STOP_LEVEL.

python tools/hunt_luga.py [stop_level=18] [extra=1] [--no-walk] [--all]
  - идёт от «Склада» Элендора по пути из карт MUD Mapper (tools/mapper_path.py), каждый шаг проверяет по названию комнаты (MSDP);
  - исследует зону (explore_msdp.Explorer: карта, мобы через «осмотреть») и в каждой комнате бьёт мобов не выше
    (уровень персонажа + extra); --all — бить всех;
  - на STOP_LEVEL останавливается (карта сохранена в areas/msdp/Заливные_луга.json): одеться, поучиться, дальше --all.
Безопасность: смерть/проверка присутствия -> стоп до /ok; в бою Bot.kill сам бежит при HP < 40%; отдых при HP < 50%.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from explore_msdp import BACK, CMD, OUT, Explorer  # noqa: E402
from hunt_zone import GOLD_RE, LOOT_RE, XP_RE, mob_key  # noqa: E402
import mapper_path  # noqa: E402

ZONES = ["Город Элендор", "Дорога Элендор - Геолант", "Окружная дорога", "Заливные луга", "Окрестные поля"]
RU2D = {v: k for k, v in CMD.items()}


class LevelReached(Exception):
    pass


# Потолок опыта за моба по уровню персонажа (data/db/exp_levels.md): моб равного/выше уровня даёт потолок, слабее — меньше
CAP = {1: 1, 2: 1, 3: 2, 4: 3, 5: 5, 6: 10, 7: 17, 8: 31, 9: 55, 10: 97, 11: 171, 12: 297, 13: 517, 14: 902, 15: 1582,
       16: 2782, 17: 4824, 18: 8404, 19: 14698, 20: 25798, 21: 45425, 22: 79211, 23: 138666, 24: 243591, 25: 429233}
LOW_YIELD = 0.4                                   # вид, давший меньше 40% потолка (слабый моб или «замакс»), больше не бьём (польз. 03.11)


def add_mob(info, zone):
    """Осмотренный бот-ом моб (`см слово`) -> data/db/mobs.csv (если такого имени ещё нет); колонки как у build_db."""
    import csv
    from build_db import DB, MOB_COLS
    name = info.get("name")
    if not name or not str(info.get("level", "")).isdigit():
        return
    path = os.path.join(DB, "mobs.csv")
    rows = list(csv.reader(open(path, encoding="utf-8-sig"), delimiter=";")) if os.path.exists(path) else [MOB_COLS]
    if any(r and r[0] == name for r in rows[1:]):
        return
    d = {"имя": name, "уровень": info["level"], "профессия": info.get("prof", ""), "особенности": info.get("flags", ""),
         "навыки": info.get("skills", ""), "логи": "бот:" + zone}
    rows.append([d.get(c, "") for c in MOB_COLS])
    os.makedirs(DB, exist_ok=True)
    csv.writer(open(path, "w", encoding="utf-8-sig", newline=""), delimiter=";").writerows(rows)


class BarbHunter(Explorer):
    def __init__(self, stop_level=18, extra=1, kill_all=False):
        super().__init__()
        self.stop_level, self.extra, self.kill_all = stop_level, extra, kill_all
        self.min_lv, self.max_lv = 0, None            # --min/--max: бить мобов этих уровней (вместо «уровень + extra»)
        self.skip_below = 2                           # --skip N: мобов уровня <= N не бить (по умолчанию 2)
        self.mv_max = 0
        self.level = None
        self._lu = 0
        self._fought = None
        self.total = {"kills": 0, "xp": 0, "gold": 0}
        self.yields = {}                              # имя вида (нижний регистр) -> опыт за последнее убийство на текущем уровне
        self._yl = None

    # ---- опыт по видам: слабых и «замаксившихся» не бьём, пока уровень не вырастет (польз. 02.11)
    def note_yield(self, name, xp):
        if self._yl != self.level:
            self.yields.clear()
            self._yl = self.level
        if name:
            self.yields[name.lower()] = xp
            self._save_yield(name.lower(), xp)

    # история опыта по видам и уровням: data/yields.json {имя: {уровень: опыт}}
    _YF = os.path.join(HERE, "..", "data", "yields.json")

    def _yhist(self):
        if getattr(self, "_h", None) is None:
            try:
                self._h = json.load(open(self._YF, encoding="utf-8"))
            except Exception:
                self._h = {}
        return self._h

    def _save_yield(self, name, xp):
        h = self._yhist()
        d = h.setdefault(name, {})
        d[str(self.level)] = max(xp, d.get(str(self.level), 0))
        try:
            json.dump(h, open(self._YF, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass

    def capped(self, name, mlevel=0):
        """Опыт = потолок МОЕГО уровня при уровне моба >= мой-2 (анализ 361 убийства, 03.11). Моб с уровнем >= мой-1 останется
        «полным» и на следующем уровне, но даст потолок побольше: его выгоднее оставить до повышения. Моб на мой-2 на следующем
        уровне даст уже ~55%: его бьём сейчас."""
        if getattr(self, "survey", False):
            return False
        cap = CAP.get(self.level)
        xp = self._yhist().get((name or "").lower(), {}).get(str(self.level))
        if not (cap and xp is not None and xp >= 0.98 * cap and getattr(self, "save_capped", False)):
            return False
        return int(mlevel or 0) >= self.level - 1 if mlevel else True

    def low_yield(self, name):
        if getattr(self, "survey", False):
            return False                       # режим разведки: бить всех подходящих по уровню, фильтр «мало опыта» выключен
        cap = CAP.get(self.level)
        last = self.yields.get((name or "").lower())
        return bool(cap and last is not None and last < LOW_YIELD * cap)

    # ---- состояние
    def wait_alarm(self):
        """Проверка присутствия/смерть: ждём человека (/ok в консоли бота)."""
        flag = os.path.join(HERE, "..", "alarm.flag")      # пишет клиент бота при подозрении на проверку присутствия
        first = True
        while os.path.exists(flag):
            if first:
                print("ТРЕВОГА (проверка присутствия): жду /ok от пользователя в консоли бота", flush=True)
                first = False
            time.sleep(2)
            self.pump(0.2)
        self.cure_blind()

    def cure_blind(self):
        """Ослепли и не прозрели -> эликсир прозрения (польз.: покупать у алхимика и следить за ними); нет эликсира — ждём."""
        state = False
        for l in self.bot.history[-60:]:
            if "Вы ослепли" in l:
                state = True
            elif "Вы прозрели" in l:
                state = False
        if not state or time.time() - getattr(self, "_blind_try", 0) < 20:
            return
        self._blind_try = time.time()
        out = " ".join(self.answer("осуш прозр", 1.5))
        print("  слепота: осуш прозр" + ("" if "Вы осушили" in out or "прозрели" in out else " (нет эликсира?)"), flush=True)

    def sync_level(self):
        if self.level is None:
            out = " ".join(self.answer("счет", 1.5))
            m = re.search(r"(\d+) уровня", out)
            if not m:
                sys.exit("не удалось прочитать уровень (сч)")
            self.level = int(m.group(1))
            self._lu = self.bot.levelups
        else:
            self.level += self.bot.levelups - self._lu
            self._lu = self.bot.levelups

    # ---- дорога
    def walk(self, steps):
        self.last_msdp_from_log()
        if not self.cur:
            sys.exit("нет MSDP-комнаты (бот запущен?)")
        for i, (d, name) in enumerate(steps):
            D = RU2D[d]
            for attempt in range(4):
                self.wait_alarm()
                if self.move(D) or (self.open_door(D) and self.move(D)):
                    break
                self.safe()
            else:
                sys.exit(f"застряли на шаге {i + 1}/{len(steps)} ({d}) в «{self.cur['name']}»")
            if self.cur["name"] != name:
                sys.exit(f"шаг {i + 1}: ждали «{name}», пришли в «{self.cur['name']}» ({self.cur['vnum']}) — стоп")
            if self.bot.status and self.bot.status.hp < 0.6 * self.bot.max_hp:
                self.safe()
        print(f"дошли: {self.cur['vnum']} {self.cur['area']} | {self.cur['name']}", flush=True)

    # ---- бой
    def known_names(self):
        """Название моба (как в «осмотреть») -> данные: из осмотров этого прохода, сохранённой карты и таблицы лога пользователя."""
        if getattr(self, "_names", None) is None or len(self.mobs) != getattr(self, "_names_n", -1):
            names = {}
            seed = os.path.join(HERE, "..", "areas", "inc", "луга_осмотры.csv")      # все осмотренные мобы лугов (лог «луга»)
            if os.path.exists(seed):
                import csv
                for row in csv.DictReader(open(seed, encoding="utf-8-sig"), delimiter=";"):
                    if row.get("Ур", "?").isdigit():
                        names[row["Имя"].lower()] = {"name": row["Имя"], "level": row["Ур"], "flags": "",
                                                     "skills": row.get("Навыки", "")}
            try:                                                   # все мобы из базы (mob_cards): известного моба не осматриваем, сразу бьём (польз. 03.11)
                import sqlite3
                _db = sqlite3.connect(os.path.join(HERE, "..", "data", "game.db"))
                for nm, lv, pf, sk in _db.execute("select name,level,prof,skills from mob_cards"):
                    if nm and len(nm) >= 4 and lv:
                        names.setdefault(nm.lower(), {"name": nm, "level": str(lv), "prof": pf or "", "flags": "", "skills": sk or ""})
                _db.close()
            except Exception:
                pass
            for m in self.mobs.values():
                if m.get("name") and int(m.get("level") or 0):
                    names[m["name"].lower()] = m
            self._names, self._names_n = names, len(self.mobs)
        return self._names

    def target(self, line):
        m = self.mobs.get(mob_key(line))
        if not m or not m.get("word") or not int(m.get("level") or 0):
            low = line.lower()                # строка с действием («Юркая сколопендра пробегает мимо.») -> по названию моба
            names = self.known_names()
            hit = next((n for n in sorted(names, key=len, reverse=True) if n in low), None)
            if not hit:
                return None
            m = dict(names[hit])
            m["word"] = [w for w in hit.split() if w not in ("с", "в", "и", "на")][-1]       # «сколопендра» (N.слово — это номер цели)
        if "Мирный" in m.get("flags", ""):
            return None
        lv = int(m.get("level") or 0)
        if lv <= self.skip_below:          # сюжетные/ловушки (на низких уровнях --skip 0)
            return None
        if self.max_lv is not None:
            if lv < self.min_lv or lv > self.max_lv:
                return None
        elif not self.kill_all and lv > self.level + self.extra:
            return None
        return m

    _tried = set()

    def names_match(self, line):
        low = line.lower()
        return any(n in low for n in self.known_names())

    def find_by_number(self, line, first=2):
        """Карточка моба строки комнаты через `см 1.`, `см 2.` … (нумерация: сначала мобы, потом игроки и предметы).
        Возвращает (слово_цели, строки_карточки) или None. Слово цели — последнее слово имени из карточки («паучок»)."""
        low = line.lower()
        order = [n for n in dict.fromkeys([max(first, 1), max(first, 1) + 1, 1]) if n <= 12]      # свой номер по списку (я = 1., моб со 2.), ещё соседний и 1. (вошёл позже); не больше 3 `см N.` (польз. 03.11)
        for n in order:
            n0 = len(self.bot.history)
            self.c.send(f"см {n}.")
            t0 = time.time()
            while time.time() - t0 < 3:
                self.pump(0.2)
                out = self.bot.history[n0:]
                if any(l.startswith(("Вы не видите", "Предмет '")) or re.search(r"в \S+ состоянии\.$", l) for l in out):
                    break
            self.pump(0.2)
            out = self.bot.history[n0:]
            card = next((re.match(r"^(.+?) \[уровень (\d+)\]", l.strip()) for l in out if re.match(r"^(.+?) \[уровень (\d+)\]", l.strip())), None)
            if not card:
                if any(l.startswith("Вы не видите") for l in out):
                    return None                              # номеров больше нет
                continue                                     # это я сама или предмет: в клетке 1. — обычно ты, вошедший моб становится 1. (правило пользователя)
            word = [w for w in card.group(1).lower().split() if w not in ("с", "в", "и", "на")][-1]
            if n == max(first, 1) or word[:5] in low:      # на своём номере берём карточку как есть: в строке комнаты часто описание («Мужик средних лет…» = Рыболов), имени в ней нет (польз. 03.11)
                return word, out
        return None

    HOLD = re.compile(r"придерж|молчан|слепот|обезд|оцепен|паралич|страх|сон")
    THING = re.compile(r"портал|доск[аи]|объявлен|указател|сундук|ларец|фонтан|статуя|алтарь|костер|кострище|скамь|стол\b|учител|^труп\b|гнездо", re.I)  # учитель в школе — квестер, не бить

    def pick(self, r):
        """Первая цель комнаты; моб с холдом/молчанием/слепотой — только если он в комнате один (смерть Эсхирда 01.11: файтер + кастер)."""
        guard = getattr(self, "guard", ())
        if guard and any(g in l.lower() for g in guard for l in r.mobs):
            return None                                   # в клетке стоит тот, кто вступится за мобов (капитан): никого не бьём (польз. 03.11)
        for line in r.mobs:
            if re.match(r"^(Ваш|Ваше|Ваша|Вы |Вас |У вас|Кто-то)", line.strip()) or re.search(r"лежит|лежат|валяется|валяются", line):
                continue                                  # эффекты на мне и предметы/трупы — не мобы
            if self.THING.search(line):
                continue                                  # предмет, а не моб (портал, доска…): не осматривать (польз. 03.11)
            if any(n in line.lower() for n in getattr(self, "never", ())):
                continue                                  # квестовые NPC (капитан, отшельник…) не трогать (польз. 03.11)
            if getattr(self, "once", False) and mob_key(line) in getattr(self, "killed_kinds", ()):
                continue                                  # разведка «по разу»: вид уже убит, опыт записан (польз. 03.11)
            m = self.target(line)
            if not m and mob_key(line) not in self._tried:
                self._tried.add(mob_key(line))        # перед боем каждый вид один раз осматриваем (`см имя`): уровень решает, бить ли (польз. 03.11)
                idx = 2                                                      # я = 1., верхний моб = 2., строка с [N] занимает N номеров (правило пользователя)
                for prev in r.mobs:
                    if prev == line:
                        break
                    mm = re.search(r"\[(\d+)\]", prev)
                    idx += int(mm.group(1)) if mm else 1
                word, out = self.find_by_number(line, idx) or self.find_keyword(mob_key(line))      # польз. 03.11: карточка по номеру (`см 2.`), бить потом по имени
                info = {"look": mob_key(line), "word": word or "", "room": r.name, "vnum": self.cur["vnum"]}
                for l in out:
                    s = l.strip()
                    mm = re.match(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$", s)
                    if mm and "name" not in info:
                        info.update(name=mm.group(1), level=mm.group(2), prof=mm.group(3) or "")
                    if s.startswith("Особенности:"):
                        info["flags"] = s.split(":", 1)[1].strip()
                    if s.startswith("Навыки:"):
                        info["skills"] = s.split(":", 1)[1].strip()
                self.mobs[mob_key(line)] = info
                add_mob(info, self.cur["area"])
                try:
                    import gamedb
                    gamedb.card(self.cur["area"], info, out)          # карточка в game.db (имя, уровень, профессия, хиты, вид, описание)
                except Exception as e:
                    print(f"  (game.db: {e})", flush=True)
                print(f"  осмотрен: {info.get('name', '?')} ур {info.get('level', '?')} ({info.get('prof', '')})", flush=True)
                m = self.target(line)
            if not m:
                continue
            if getattr(self, "once", False) and (m.get("name") or "").lower() in getattr(self, "killed_names", ()):
                continue                                  # моб с таким именем уже убит и записан: по одному на имя (польз. 03.11)
            if self.HOLD.search(m.get("skills", "")) and len(r.mobs) > 1:
                continue
            return m
        return None

    def rest_up(self, frac=0.9):
        st = self.bot.status
        if st and st.hp < 0.7 * self.bot.max_hp and not st.in_battle:
            self.send("отдыхать", 1)
            t0 = time.time()
            while self.bot.status and self.bot.status.hp < frac * self.bot.max_hp and time.time() - t0 < 300:
                self.pump(4)
                if self.bot.status and self.bot.status.in_battle:
                    break
            self.send("встать", 1)

    def fight_here(self):
        fresh = True
        for _ in range(12):
            self.wait_alarm()
            if not fresh:
                self.look()                    # после убийства — один раз обновить список мобов
            fresh = False
            r = self.last_room
            if not r or not self.cur or r.name != self.cur["name"]:
                return
            mob = self.pick(r)
            if not mob:
                return
            self.rest_up()                     # на бой — только с HP не ниже 70%
            n0, t0 = len(self.bot.history), time.time()
            won = self.bot.kill(mob["word"])
            secs = round(time.time() - t0, 1)
            if self.bot.dead:
                sys.exit("ПЕРСОНАЖ ПОГИБ: охота остановлена")
            if not won:
                self.last_msdp_from_log()
                self.safe()
                return
            self.pump(0.3)                      # лут подбирает триггер «R.I.P. -> взять все»
            out = self.bot.history[n0:]
            xp = sum(int(m.group(1)) for l in out if (m := re.search(r"Вы получили (\d+) единиц", l)))   # не ждать опоздавшую строку (польз. 03.11): пропущенное добирает tools/backfill_exp.py из out.log
            gold = sum(int(m.group(1)) for l in out if (m := GOLD_RE.match(l)))
            got = [m.group(1) for l in out if (m := LOOT_RE.match(l)) and not l.startswith("Вы взяли кучку монет")]
            self.total["kills"] += 1
            self.total["xp"] += xp
            self.total["gold"] += gold
            self.sync_level()
            self.note_yield(mob.get("name") or mob.get("look"), xp)
            if not hasattr(self, "killed_kinds"):
                self.killed_kinds = set()
            self.killed_kinds.add(mob.get("look") or mob["word"])
            if not hasattr(self, "killed_names"):
                self.killed_names = set()
            self.killed_names.add((mob.get("name") or "").lower())
            try:
                import gamedb
                gamedb.kill(self.cur["area"], mob.get("name") or mob.get("look"), mob.get("level"), self.level, xp, secs)       # опыт за каждое убийство
            except Exception as e:
                print(f"  (game.db: {e})", flush=True)
            print(f"  убит {mob.get('name') or mob['look']} (ур {mob.get('level')}) за {secs} с: опыт {xp}, монет {gold}"
                  f"{', ' + ', '.join(got) if got else ''}  [ур {self.level}, всего {self.total['kills']}]", flush=True)
            self.safe()
            if self.level >= self.stop_level:
                raise LevelReached()

    def move(self, d):
        """Как Explorer.move, но без лишних пауз: описание комнаты приходит сразу за MSDP."""
        before = self.cur["vnum"] if self.cur else None
        if "#" in self.map_cell(d):
            self.known_dt.setdefault(before, set()).add(d)
            return False
        for attempt in range(2):
            n0 = len(self.bot.history)
            self.c.send(CMD[d])
            t0 = time.time()
            while time.time() - t0 < 6:
                self.pump(0.1)
                if self.cur and self.cur["vnum"] != before:
                    t1 = time.time()                    # ждём, пока разберётся описание НОВОЙ комнаты (иначе fight_here видит старую)
                    while time.time() - t1 < 1.6:
                        self.pump(0.1)
                        if self.last_room and self.last_room.name == self.cur["name"]:
                            self.pump(0.1)
                            break
                    return True
                if any(" не пускает вас" in l for l in self.bot.history[n0:]):
                    break
            guard = next((m.group(1) for l in self.bot.history[n0:]
                          if (m := re.match(r"^(.+?) не пускает вас", l))), None)
            if not guard or attempt:
                return False
            if not self.bot.kill(guard.split()[-1].lower()):
                return False
        return False

    def safe(self):
        """HP (как у Explorer) + энергия: при V < 40 отдыхаем, чтобы не тратить настойки восстановления."""
        super().safe()
        st = self.bot.status
        if st:
            self.mv_max = max(self.mv_max, st.mv)
        if st and st.mv < 0.3 * max(self.mv_max, 60) and not st.in_battle:
            self.send("отдыхать", 1)
            t0 = time.time()
            while self.bot.status and self.bot.status.mv < 0.8 * self.mv_max and time.time() - t0 < 240:
                self.pump(5)
                if self.bot.status and self.bot.status.in_battle:
                    break
            self.send("встать", 1)

    def inspect_mobs(self, node):
        super().inspect_mobs(node)
        v = self.cur["vnum"]
        if self._fought != v:
            self._fought = v
            self.fight_here()


def load_map(h, zone="Заливные_луга"):
    d = json.load(open(os.path.join(OUT, zone + ".json"), encoding="utf-8"))
    h.rooms = d["rooms"]
    h.mobs = {**d.get("mobs", {}), **h.mobs}
    return d


def hunt_pass(h):
    """Один проход по сохранённой карте: всегда ближайшая комната, где ещё не были за проход, бой в каждой."""
    h.last_msdp_from_log()
    seen = set()
    while True:
        h.wait_alarm()
        v0 = h.cur["vnum"]
        seen.add(v0)
        h._fought = None
        h.fight_here()
        v0 = h.cur["vnum"]
        prev, q, goal = {v0: None}, [v0], None
        while q:
            v = q.pop(0)
            if v not in seen:
                goal = v
                break
            for d, t in h.rooms.get(v, {}).get("exits", {}).items():
                if d in CMD and t in h.rooms and t not in prev and (v, d) not in h.bad:
                    prev[t] = (v, d)
                    q.append(t)
        if not goal:
            return len(seen)
        path, v = [], goal
        while prev[v]:
            v, d = prev[v]
            path.append(d)
        for d in path[::-1]:
            before = h.cur["vnum"]
            if not h.move(d) and not (h.open_door(d) and h.move(d)):
                h.bad.add((before, d))
                h.safe()
                break
            if h.bot.status and h.bot.status.in_battle:
                h.safe()
        seen.add(h.cur["vnum"])


def go_home(h):
    """Из любой комнаты лугов на склад Элендора: по карте лугов до «По краю болота» (vnum 140001), дальше по картам маппера."""
    load_map(h)
    h.last_msdp_from_log()
    if h.cur["area"] == "Заливные луга" and h.cur["vnum"] != "140001":
        prev, q = {h.cur["vnum"]: None}, [h.cur["vnum"]]
        while q:
            v = q.pop(0)
            if v == "140001":
                break
            for d, t in h.rooms.get(v, {}).get("exits", {}).items():
                if d in CMD and t in h.rooms and t not in prev:
                    prev[t] = (v, d)
                    q.append(t)
        path, v = [], "140001"
        while prev.get(v):
            v, d = prev[v]
            path.append(d)
        for d in path[::-1]:
            if not h.move(d):
                h.safe()
                if not h.move(d):
                    sys.exit(f"застряли на пути к выходу из лугов ({CMD[d]}) в «{h.cur['name']}»")
    res = mapper_path.route(ZONES, "Заливные луга", "По краю болота", "Город Элендор", "Склад", start_id=1)
    if not res:
        sys.exit("пути домой по картам нет")
    h.walk([(d, n) for d, n, _ in res[2]])


def main():
    skip = {sys.argv.index(o) + 1 for o in ("--min", "--max", "--skip") if o in sys.argv}      # значения после --min/--max/--skip
    args = [a for i, a in enumerate(sys.argv) if i and not a.startswith("--") and i not in skip]
    stop = int(args[0]) if args else 18
    extra = int(args[1]) if len(args) > 1 else 1
    h = BarbHunter(stop, extra, "--all" in sys.argv)
    for opt in ("--min", "--max"):
        if opt in sys.argv:
            setattr(h, "min_lv" if opt == "--min" else "max_lv", int(sys.argv[sys.argv.index(opt) + 1]))
    if "--skip" in sys.argv:
        h.skip_below = int(sys.argv[sys.argv.index("--skip") + 1])
    h.sync_level()
    if "--home" in sys.argv:
        go_home(h)
        return
    print(f"уровень {h.level}, стоп на {stop}, бью мобов до ур {'любых' if h.kill_all else h.level + extra}", flush=True)
    if "--no-walk" not in sys.argv:
        res = mapper_path.route(ZONES, "Город Элендор", "Склад", "Заливные луга", "По краю болота")
        if not res:
            sys.exit("пути по картам нет")
        _, _, path = res
        h.walk([(d, n) for d, n, _ in path])
    t0 = time.time()
    try:
        if "--hunt" in sys.argv:
            load_map(h)
            n = 0
            while True:
                n += 1
                k0, x0 = h.total["kills"], h.total["xp"]
                t1 = time.time()
                rooms = hunt_pass(h)
                print(f"проход {n}: комнат {rooms}, убито {h.total['kills'] - k0}, опыт {h.total['xp'] - x0}, "
                      f"{int(time.time() - t1)} с", flush=True)
                if time.time() - t1 < 120 and h.total["kills"] == k0:      # пусто: ждём репоп
                    print("мобов нет, жду репоп 5 мин (отдых)", flush=True)
                    h.send("отдыхать", 1)
                    for _ in range(60):
                        h.pump(5)
                    h.send("встать", 1)
            area = h.cur["area"]
        area, start = h.explore()
        h.save(area, start)
        print("зона исследована и пройдена", flush=True)
    except LevelReached:
        area, start = h.cur["area"], None
        h.save(area, h.cur["vnum"])
        print(f"ДОСТИГНУТ {h.level} УРОВЕНЬ: стоп. Карта сохранена.", flush=True)
    secs = int(time.time() - t0)
    print(f"за {secs // 60} мин: убито {h.total['kills']}, опыт {h.total['xp']}, монет {h.total['gold']}", flush=True)


if __name__ == "__main__":
    main()


