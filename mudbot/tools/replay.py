"""Проиграть маршрут из лога пользователя (tools/mk_route.py -> data/db/routes/<имя>.json): идти и бить.

python tools/replay.py <маршрут> [--stop N] [--from K] [--to K] [--here] [--no-kill]
  --stop N   остановиться на уровне N        --from/--to  срез шагов (номера по списку шагов маршрута)
  --here     не идти на старт (маршрут стартует с Склада Элендора, 100076; без --here идём туда сами)
  --debug    отладка на сильном персонаже: бить всех мобов из лога (фильтры «мало опыта»/ниже уровня выключены)
Ходьба — пачками «север;восток;...» (спидволк), сверка по названию комнаты в конце пачки. Убийства — по именам из лога
(`убить <слово>`); незнакомых мобов осматриваем `смотреть <слово>` и дописываем в data/db/mobs.csv. Безопасность как у
hunt_luga: смерть -> стоп, HP < 70% отдых перед боем, проверка присутствия -> ждём.
"""
import csv
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_db import DB  # noqa: E402
from explore_msdp import CMD  # noqa: E402
from hunt_luga import BarbHunter, add_mob  # noqa: E402
from mapfight import MapHunter, allowed  # noqa: E402
from hunt_zone import GOLD_RE, LOOT_RE, XP_RE  # noqa: E402

RU2D = {v: k for k, v in CMD.items()}
HOME = "100076"          # Склад Элендора


class Replay(MapHunter):
    def __init__(self, stop):
        super().__init__(stop, 0, allowed(["all"]))       # extra 0: мобов выше своего уровня не бьём (потолок опыта, польз. 02.11)
        self.skip_below = 0
        self.known = self.db_names()
        self.fails = {}

    def db_names(self):
        path = os.path.join(DB, "mobs.csv")
        if not os.path.exists(path):
            return set()
        return {r[0].lower() for r in csv.reader(open(path, encoding="utf-8-sig"), delimiter=";") if r and r[0]}      # все мобы из логов (убиты там)

    def study(self, name, word):
        """Моб из лога, которого нет в БД: `смотреть слово` -> строка «Имя [уровень N], Профессия» + Особенности/Навыки."""
        out = self.answer("смотреть " + word, 1.5)
        info = {}
        for l in out:
            s = l.strip()
            mm = re.match(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$", s)
            if mm and "name" not in info:
                info.update(name=mm.group(1), level=mm.group(2), prof=mm.group(3) or "")
            if s.startswith("Особенности:"):
                info["flags"] = s.split(":", 1)[1].strip()
            if s.startswith("Навыки:"):
                info["skills"] = s.split(":", 1)[1].strip()
        if info.get("name"):
            add_mob(info, self.cur["area"])
            self.known.add(info["name"].lower())
            print(f"  в БД: {info['name']} ур {info['level']} {info.get('prof', '')}", flush=True)
            return info
        return None

    def keywords(self, name):
        """Слова для `убить`: последнее слово названия; у «Кобольд-воин» — и вся связка, и обе части."""
        w = name.lower().split()[-1]
        parts = [w] + [p for p in re.split(r"[-]", w) if p and p != w][::-1]
        return parts

    # ---- ходьба
    def go(self, moves, room_end):
        """Пачка шагов: уходит одной строкой, ждём конец очереди; True если пришли в комнату room_end."""
        self.wait_alarm()
        st = self.bot.status
        if st and st.in_battle:
            self.safe()
        self.c.send(";".join(m for m in moves))
        t0, last, quiet = time.time(), None, 0.0
        hidden = room_end.startswith("* скрытая")        # в логе пользователя название клетки скрыто: сверять нечем, верим MSDP
        while time.time() - t0 < 5 + 1.3 * len(moves):
            self.pump(0.2)
            v = self.cur["vnum"] if self.cur else None
            quiet = quiet + 0.2 if v == last else 0.0
            last = v
            if self.cur and (hidden or self.cur["name"] == room_end) and quiet >= 0.6:
                break
            if quiet >= 3.0:
                break
        self.pump(0.3)
        return bool(self.cur) and (hidden or self.cur["name"] == room_end)

    def goto_home(self):
        import goto as g
        self.last_msdp_from_log()
        if self.cur["vnum"] != HOME:
            print(f"иду на Склад из {self.cur['vnum']} {self.cur['name']}", flush=True)
            if not g.goto(self, HOME):
                sys.exit("не дошли до Склада")

    def level_of(self, name):
        """Уровень моба из БД (mobs.csv / осмотр ботом) или 0, если неизвестен."""
        for m in self.mobs.values():
            if (m.get("name") or "").lower() == name.lower() and str(m.get("level", "")).isdigit():
                return int(m["level"])
        return 0

    # ---- шаги
    def kill_names(self, names):
        want = {}
        for n in names:
            want[n] = want.get(n, 0) + 1
        for name, cnt in want.items():
            kws = self.keywords(name)
            if (name.lower() not in self.known or not self.level_of(name)) and self.cur:
                for kw in kws:
                    if self.study(name, kw):
                        break
            lv = self.level_of(name)
            if lv and lv > self.level + self.extra:
                print(f"  пропуск {name} (ур {lv} > мой {self.level}): оставляем на потом", flush=True)
                continue
            if lv and lv < self.level - self.below:
                print(f"  пропуск {name} (ур {lv} < мой {self.level} - {self.below}): даёт мало опыта", flush=True)
                continue
            if self.low_yield(name):
                print(f"  пропуск {name}: даёт мало опыта на {self.level} лвл", flush=True)
                continue
            if self.capped(name, lv):
                print(f"  пропуск {name}: даёт потолок {self.level} лвл, оставляем до следующего уровня", flush=True)
                continue
            done = 0
            for _ in range(cnt + 1):
                if self.low_yield(name):
                    break
                self.wait_alarm()
                self.rest_up()
                won = False
                for kw in kws:
                    n0 = len(self.bot.history)
                    t0 = time.time()
                    won = self.bot.kill(kw)
                    if self.bot.dead:
                        sys.exit("ПЕРСОНАЖ ПОГИБ: стоп")
                    if won or (self.bot.status and self.bot.status.in_battle):
                        break
                if not won:
                    self.safe()
                    break
                done += 1
                self.pump(0.3)
                out = self.bot.history[n0:]
                xp = sum(int(m.group(1)) for l in out if (m := XP_RE.match(l)))
                self.total["kills"] += 1
                self.total["xp"] += xp
                self.sync_level()
                self.note_yield(name, xp)
                print(f"  убит {name} за {round(time.time() - t0, 1)} с: опыт {xp} [ур {self.level}, всего {self.total['kills']}]",
                      flush=True)
                self.safe()
                if self.level >= self.stop_level:
                    return True
            if done < cnt:
                self.fails[name] = self.fails.get(name, 0) + (cnt - done)
        return False

    def walk_steps(self, steps, no_kill=False):
        i, n = 0, len(steps)
        while i < n:
            s = steps[i]
            if "move" in s:
                j = i
                while j < n and "move" in steps[j] and j - i < 8:
                    j += 1
                chunk = steps[i:j]
                if self.go([m["move"] for m in chunk], chunk[-1]["room"]):
                    i = j
                    continue
                # не пришли: возможно, мы где-то внутри пачки (дверь, бой) — ищем текущую комнату среди шагов пачки
                name = self.cur["name"]
                idx = next((k for k in range(len(chunk) - 1, -1, -1) if chunk[k]["room"] == name), None)
                if idx is not None:
                    i += idx + 1
                    continue
                self.safe()
                self.last_msdp_from_log()
                if self.cur["name"] == chunk[-1]["room"]:
                    i = j
                    continue
                sys.exit(f"сбились на шаге {i}: ждали «{chunk[-1]['room']}», мы в «{self.cur['name']}» ({self.cur['vnum']})")
            elif "kill" in s:
                if not no_kill and self.kill_names(s["kill"]):
                    return True
                i += 1
            else:
                cmd = s["cmd"]
                if "<направление>" in cmd or cmd.startswith("область информация"):
                    # в лог попала справка команды `обл` (Использование: …), а не сама команда: создаём область сами
                    nxt = next((x["move"] for x in steps[i + 1:] if "move" in x), None)
                    cmd = f"область создать {nxt}" if cmd.startswith("область создать") and nxt else None
                if cmd is None or (os.environ.get("BARB_SKIP_PREP") and cmd.startswith(("кз :колбы", "кз :следак1", "кз :барб", "кз :сел", "кз :общий"))) \
                        or cmd.startswith(("кз ", "кс ", "ксклад", "ксдать", "кзабрать", "клан ", "переслать ", "осмотреть доска", "осм доска")):
                    i += 1       # одежду и расходники ведёт barb_levelup.py (по уровню), а не лог пользователя
                    continue
                print(f"  команда: {cmd}", flush=True)
                a0 = self.cur["area"]
                self.c.send(cmd)
                self.pump(5 if "област" in cmd else 1.8)      # область создаётся не сразу
                self.last_msdp_from_log()
                if cmd.startswith("ехать"):             # повозка едет минуту-две: ждём, пока выйдем из «Тарантаса»
                    t0 = time.time()
                    while time.time() - t0 < 300 and (self.cur["name"] == "Тарантас" or self.cur["area"] == a0):
                        self.pump(1)
                        self.last_msdp_from_log()
                    self.pump(2)
                    self.last_msdp_from_log()
                i += 1
            if i % 25 == 0:
                print(f"шаг {i}/{n}: {self.cur['name']}, убито {self.total['kills']}, опыт {self.total['xp']}", flush=True)
        return False


def main():
    args = [a for k, a in enumerate(sys.argv) if k and not a.startswith("--") and sys.argv[k - 1] not in ("--stop", "--from", "--to")]
    name = args[0]
    opt = lambda o, d=None: int(sys.argv[sys.argv.index(o) + 1]) if o in sys.argv else d
    route = json.load(open(os.path.join(DB, "routes", name + ".json"), encoding="utf-8"))
    steps = route["steps"][opt("--from", 0):opt("--to")]
    r = Replay(opt("--stop", 99))
    r.sync_level()
    if "--debug" in sys.argv:           # отладка маршрута на сильном персонаже: бить всех из лога, фильтры уровня/опыта выключены
        r.survey, r.skip_below, r.below = True, 99, 99
    r.last_msdp_from_log()
    if "--here" not in sys.argv:
        r.goto_home()
    print(f"маршрут {name}: {len(steps)} шагов, уровень {r.level}, стоп на {r.stop_level}", flush=True)
    t0 = time.time()
    reached = r.walk_steps(steps, "--no-kill" in sys.argv)
    print(f"{'ДОСТИГНУТ ' + str(r.level) + ' УРОВЕНЬ' if reached else 'маршрут пройден'} за {int(time.time() - t0)} с: "
          f"убито {r.total['kills']}, опыт {r.total['xp']}; не нашли: {r.fails}", flush=True)


if __name__ == "__main__":
    main()



