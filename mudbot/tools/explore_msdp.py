"""Изучение зоны по MSDP (номера комнат, зона, выходы) через работающего бота (inbox.txt / out.log).

python tools/explore_msdp.py              -> изучает зону, в которой стоит персонаж
Результат: areas/msdp/<vnum зоны>_<название>.json (комнаты, выходы, мобы, скрытые выходы, подозрения на ДТ),
           areas/msdp/..._map.txt (карта по координатам), areas/msdp/..._mobs.csv.

Безопасность:
  * в другую зону не заходим (AREA соседней комнаты другая -> шаг назад, выход помечен «граница»);
  * если в описании комнаты есть слова-подсказки смертельной ловушки, неизвестные выходы из неё не трогаем;
  * HP < 50% -> бежать/отдыхать, «Вы мертвы» -> немедленный выход;
  * скрытые выходы берём из MSDP (есть в EXITS, нет в [ Exits ]): записываем, но не ходим туда.
"""
import ast
import csv
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from explore_zone import FileClient  # noqa: E402
from mudbot.bot import Bot  # noqa: E402
from mudbot.parser import RoomParser, is_map_line, parse_exits  # noqa: E402

OUT = os.path.join(ROOT, "areas", "msdp")
WALKED = os.path.join(OUT, "_walked.json")      # все комнаты, увиденные по MSDP (для goto)
CMD = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
BACK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
VEC = {"N": (0, -1, 0), "S": (0, 1, 0), "E": (1, 0, 0), "W": (-1, 0, 0), "U": (0, 0, 1), "D": (0, 0, -1)}
DT_WORDS = re.compile(r"пропаст|обрыв(?!к|ает)|бездн|трясин|\bлав[аыу]\b|кипящ|зыбуч|водоворот|смертельн|пропасть|пучин"
                      # прямые предупреждения в тексте (Развалины 101053 -> ДТ «В конце туннеля»)
                      r"|прекратить (этот )?путь|поверн\w* назад|не вернул|не возвраща|зря вы|стоит ли")
MSDP_RE = re.compile(r"^\[msdp\] комната (\d+) \| (.*?) \| (.*?) \| (\{.*\})\s*$")
LOOK_OK = re.compile(r"^Вы видите перед собой|состоянии\.$")
# слова строки моба, которые точно не имя (глаголы позы, места)
NOT_NAME = {"тут", "здесь", "стоит", "сидит", "лежит", "летает", "ходит", "бродит", "ползет", "жужжит", "снует",
            "порхает", "смотрит", "вас", "вам", "свои", "туда", "сюда", "ветки", "веточки", "норовит", "чистит"}


def mob_words(line):
    """Кандидаты в ключевые слова по порядку строки; прилагательные (-ый/-ий/-ая/-ое…) пробуем последними."""
    words = [w for w in re.findall(r"[а-яё]+", line.lower()) if len(w) >= 3 and w not in NOT_NAME]
    adj = re.compile(r"(ый|ий|ой|ая|яя|ое|ее|ые|ие)$")
    return [w for w in words if not adj.search(w)] + [w for w in words if adj.search(w)]


class Explorer:
    def __init__(self):
        self.c = FileClient()
        self.bot = Bot(self.c)
        self.rp = RoomParser()
        self.cur = None          # {"vnum", "area", "name", "exits"}
        self.last_room = None    # Room из текста
        self.rooms = {}
        self.mobs = {}
        self.details = set()     # vnum комнат со строкой « * скрытая деталь * » (режим детали да)
        self.known_dt = {}       # vnum -> направления в ДТ из прошлых записей зоны
        self.bad = set()         # (vnum, направление), куда шаг не удался
        self.minimap = []        # последняя миникарта (строки), self.map_buf — собираемая
        self.map_buf = []

    # ---- поток строк: MSDP + текст комнаты
    def pump(self, sec):
        end = time.time() + sec
        got = False
        while time.time() < end:
            try:
                ln = self.c.lines.get(timeout=0.1)
            except Exception:
                continue
            self.bot._process(ln)
            m = MSDP_RE.match(ln.text)
            if m:
                try:
                    ex = ast.literal_eval(m.group(4))
                except Exception:
                    ex = {}
                self.cur = {"vnum": m.group(1), "area": m.group(2), "name": m.group(3), "exits": ex}
                got = True
                self.remember_walked()
            if ln.text.startswith(("Вам лучше встать на ноги", "Вы не можете это сделать, сидя")):
                self.c.send("встать")                  # сбили с ног в бою
            if is_map_line(ln.text) or (len(ln.text) >= 20 and not ln.text.strip()):   # пустой ряд карты — пробелы
                self.map_buf.append(ln.text.rstrip("\r\n"))
            elif self.map_buf:
                if len(self.map_buf) >= 13:
                    self.minimap = self.map_buf
                self.map_buf = []
            if "скрытая деталь" in ln.text and self.cur:
                self.details.add(self.cur["vnum"])
            r = self.rp.feed(ln.text)
            if r and r.name:
                self.last_room = r
            if self.bot.dead:
                sys.exit("ПЕРСОНАЖ ПОГИБ: изучение остановлено")
        return got

    def remember_walked(self):
        """Каждая комната из MSDP — в areas/msdp/_walked.json (выходы по MSDP), чтобы goto знал и пройденное
        вручную, мимо исследователя."""
        v = self.cur["vnum"]
        if not hasattr(self, "walked_db"):
            try:
                self.walked_db = json.load(open(WALKED, encoding="utf-8"))
            except Exception:
                self.walked_db = {}
        node = {"name": self.cur["name"], "area": self.cur["area"],
                "exits": {k: str(t) for k, t in self.cur["exits"].items()}}
        if self.walked_db.get(v) != node:
            self.walked_db[v] = node
            json.dump(self.walked_db, open(WALKED, "w", encoding="utf-8"), ensure_ascii=False)

    def send(self, cmd, wait=1.2):
        self.c.send(cmd)
        self.pump(wait)

    def look(self):
        self.send("смотреть", 1.0)

    def record(self):
        v = self.cur["vnum"]
        r = self.last_room
        text_exits = []
        if r and r.name == self.cur["name"]:
            text_exits = r.exits + r.hidden_exits
        node = self.rooms.setdefault(v, {"name": self.cur["name"], "area": self.cur["area"], "exits": {},
                                         "hidden": [], "doors": [], "mobs": [], "desc": "", "dt_hint": False})
        node["exits"].update({k: str(t) for k, t in self.cur["exits"].items()})
        if r and r.name == self.cur["name"]:
            node["desc"] = r.description
            node["dt_hint"] = bool(DT_WORDS.search(r.description.lower()))
            node["mobs"] = sorted(set(node["mobs"]) | set(r.mobs))
            node["doors"] = r.hidden_exits
            visible = {k for k in CMD if CMD[k] in r.exits or CMD[k] in r.hidden_exits}
            node["hidden"] = sorted(set(self.cur["exits"]) - visible)
        if node["dt_hint"] and self.minimap and all("#" not in self.map_cell(d) and "..." not in self.map_cell(d)
                                                    for d in "NSEW"):   # «...» — темно, ДТ не разглядеть
            # слово-подсказка есть («мост над пропастью»), но миникарта ДТ рядом не показывает: идём,
            # кроме вверх/вниз — их на карте не видно
            node["dt_hint"] = False
            node["dt_map_ok"] = True
            self.known_dt.setdefault(v, set()).update({"U", "D"})
        if v in self.details and not node.get("detail"):
            node["detail"] = True
            print(f"  скрытая деталь: {v} {node['name']}", flush=True)
        return node

    def answer_until(self, cmd, pat, wait=30):
        """Как answer, но выходит сразу, как в ответе встретилась строка по регулярке pat — без лишних пауз (польз.)."""
        import re as _re
        n0 = len(self.bot.history)
        self.c.send(cmd)
        end = time.time() + wait
        out = []
        while time.time() < end:
            self.pump(0.3)
            out = [l for l in self.bot.history[n0:] if not l.startswith("<<H")]
            if any(_re.search(pat, l) for l in out):
                break
        return out

    def move_cmd(self, cmd, wait=6):
        """Команда, меняющая комнату (войти портал, куп 2): ждём смены комнаты по MSDP, а не фиксированную паузу."""
        v0 = self.cur["vnum"] if self.cur else None
        self.c.send(cmd)
        end = time.time() + wait
        while time.time() < end:
            self.pump(0.3)
            if self.cur and self.cur["vnum"] != v0:
                break

    def answer(self, cmd, wait=1.2):
        """Строки ответа на команду (без статуса)."""
        n0 = len(self.bot.history)
        self.send(cmd, wait)
        return [l for l in self.bot.history[n0:] if not l.startswith("<<H")]

    def find_keyword(self, line):
        """Слово, на которое отзывается моб из строки комнаты: пробуем слова строки через «осмотреть <слово>»
        (одна команда и проверяет слово, и показывает уровень). Возвращает (слово, строки ответа)."""
        for w in list(mob_words(line))[:3]:                   # не больше 3 слов (польз. 03.11: без спама осмотрами)
            n0 = len(self.bot.history)
            self.c.send(f"осмотреть {w}")
            t0 = time.time()
            while time.time() - t0 < 3:
                self.pump(0.2)
                out = self.bot.history[n0:]
                if any(l.startswith("Вы не видите здесь") for l in out):
                    break
                if any(LOOK_OK.search(l) for l in out):     # «Вы видите перед собой …», «… состоянии.»
                    self.pump(0.3)
                    return w, self.bot.history[n0:]
        return None, []

    def inspect_mobs(self, node):
        r = self.last_room
        if not r or r.name != node["name"]:
            return
        for line in r.mobs:
            key = re.sub(r"\s+\.\.\..*$", "", line).strip()
            if key in self.mobs or key.startswith("Труп") or '"' in key:     # реплики мобов не мобы
                continue
            info = {"look": key, "room": node["name"], "vnum": self.cur["vnum"]}
            word, out = self.find_keyword(key)
            info["word"] = word or ""
            if word:
                for l in out:
                    s = l.strip()
                    m = re.match(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$", s)
                    if m and "name" not in info:
                        info.update(name=m.group(1), level=m.group(2), prof=m.group(3) or "")
                    if s.startswith("Особенности:"):
                        info["flags"] = s.split(":", 1)[1].strip()
                    if s.startswith("Навыки:"):
                        info["skills"] = s.split(":", 1)[1].strip()
                    m = re.match(r"^Хиты: (\d+)/(\d+)", s)
                    if m:
                        info["hp"] = m.group(2)
                    m = re.match(r"^Вы видите перед собой (.+?)\.$", s)
                    if m:
                        info["race"] = m.group(1)
            self.mobs[key] = info

    def safe(self):
        st = self.bot.status
        if st and st.in_battle:
            t0 = time.time()
            while self.bot.status and self.bot.status.in_battle and time.time() - t0 < 90:
                if self.bot.status.hp < 0.5 * self.bot.max_hp:
                    self.send("убежать", 2)
                self.pump(2)
        st = self.bot.status
        if st and st.hp < 0.5 * self.bot.max_hp:
            self.send("отдыхать", 1)
            t0 = time.time()
            while self.bot.status and self.bot.status.hp < 0.9 * self.bot.max_hp and time.time() - t0 < 300:
                self.pump(5)
            self.send("встать", 1)

    def map_cell(self, d=None):
        """Клетка миникарты (режим карта сверху): 3 символа, своя (d=None) или соседняя по d.
        Сетка 7x7, строки комнат — нечётные строки карты, клетка — символы 1..3 из блока в 4.
        # — ДТ, M — моб высокого уровня, m — моб, @ — персонаж (свой в центре)."""
        rows = self.minimap[1::2]
        if len(rows) != 7:
            return ""
        r, c = {None: (3, 3), "N": (2, 3), "S": (4, 3), "E": (3, 4), "W": (3, 2)}.get(d, (None, None))
        if r is None or len(rows[r]) < c * 4 + 4:
            return ""
        return rows[r][c * 4 + 1:c * 4 + 4]

    def move(self, d):
        before = self.cur["vnum"] if self.cur else None
        if "#" in self.map_cell(d):
            print(f"  миникарта: {CMD[d]} от {before} — ДТ (#), не иду", flush=True)
            if self.cur and before in self.rooms:
                self.rooms[before].setdefault("dt", {})[d] = "ДТ по миникарте"
            self.known_dt.setdefault(before, set()).add(d)
            return False
        for attempt in range(2):
            n0 = len(self.bot.history)
            self.c.send(CMD[d])
            t0 = time.time()
            while time.time() - t0 < 6:
                self.pump(0.3)
                if self.cur and self.cur["vnum"] != before:
                    self.pump(0.6)                         # дочитать описание комнаты
                    return True
                if any(" не пускает вас" in l for l in self.bot.history[n0:]):
                    break
            # «Магический голем не пускает вас на север» (голем Развалин возрождается каждые пару раундов):
            # бьём сторожа и сразу шагаем
            guard = next((m.group(1) for l in self.bot.history[n0:]
                          if (m := re.match(r"^(.+?) не пускает вас", l))), None)
            if not guard or attempt:
                return False
            print(f"  {guard} не пускает {CMD[d]}: убиваю", flush=True)
            if not self.bot.kill(guard.split()[-1].lower()):
                return False
        return False

    def last_msdp_from_log(self):
        """MSDP шлёт ROOM только при переходе: текущая комната = последняя такая строка в out.log."""
        with open(self.c.log, encoding="utf-8", errors="replace") as f:
            tail = f.read().splitlines()          # после долгой справки последняя комната может быть далеко
        for l in reversed(tail):
            m = MSDP_RE.match(l)
            if m:
                self.cur = {"vnum": m.group(1), "area": m.group(2), "name": m.group(3),
                            "exits": ast.literal_eval(m.group(4))}
                return

    def todo(self, v, tried):
        node = self.rooms[v]
        if node["dt_hint"]:
            return []
        return [d for d, t in node["exits"].items()
                if d in CMD and (v, d) not in tried and t not in self.rooms and d not in node["hidden"]
                and d not in self.known_dt.get(v, ())]

    def path_to_todo(self, tried):
        """Кратчайший путь до комнаты с непройденными выходами: по пройденным переходам и по выходам MSDP
        в уже известные комнаты (пройденный переход важнее: в лабиринте выход может вести не туда)."""
        start = self.cur["vnum"]
        prev, q = {start: None}, [start]
        while q:
            v = q.pop(0)
            if self.todo(v, tried):
                path = []
                while prev[v]:
                    v, d = prev[v]
                    path.append(d)
                return path[::-1]
            known = {d: t for d, t in self.rooms[v]["exits"].items() if d in CMD and t in self.rooms}
            known.update(self.walked.get(v, {}))
            known = {d: t for d, t in known.items() if (v, d) not in self.bad}
            for d, t in known.items():
                if t not in prev:
                    prev[t] = (v, d)
                    q.append(t)
        return None

    def open_door(self, d):
        """Дверь в направлении d: имя из «оглянуться» («На севере: железная дверь (закрыто)»), открыть,
        заперта -> отпереть (нужен ключ в инвентаре) и открыть. True, если дверь открылась."""
        stem = {"N": "север", "S": "юг", "E": "восто", "W": "запад", "U": "верх", "D": "низ"}[d]
        door = next((m.group(1) for l in self.answer("оглянуться")
                     if (m := re.match(r"^\s*(?:На )?\S*" + stem + r"\S*: (.+?) \(закрыто\)", l, re.I))), None)
        if not door:
            return False
        out, word = [], door.split()[-1]
        for w in door.split():              # «дверь в денник», «железный люк»: пробуем слова описания, пока игра не найдёт предмет
            if len(w) < 3 or w in ("в", "на", "из", "для"):
                continue
            out = self.answer(f"открыть {w} {CMD[d]}")
            if not any("нет '" in l for l in out):
                word = w
                break
        if any("заперт" in l for l in out):
            out = self.answer(f"отпереть {word} {CMD[d]}")
            if not any(l.startswith("Вы отперли") for l in out):
                print(f"  заперто, нет ключа: {self.cur['vnum']} {CMD[d]} ({door})", flush=True)
                return False
            out = self.answer(f"открыть {word} {CMD[d]}")
        ok = any(l.startswith("Вы открыли") or "открыт" in l for l in out)
        print(f"  дверь {self.cur['vnum']} {CMD[d]} ({door}): {'открыта' if ok else ' / '.join(out)[:120]}", flush=True)
        return ok

    def step(self, d):
        """Шаг с записью, куда он реально привёл (в лабиринтах MSDP-выход и итог могут не совпадать)."""
        v = self.cur["vnum"]
        if not self.move(d) and not (self.open_door(d) and self.move(d)):
            self.bad.add((v, d))          # MSDP показывает выход, а пройти нельзя — больше не планировать через него
            return False
        self.walked.setdefault(v, {})[d] = self.cur["vnum"]
        claimed = self.rooms[v]["exits"].get(d)
        if claimed and claimed != self.cur["vnum"]:
            self.rooms[v].setdefault("tricky", {})[d] = self.cur["vnum"]
        return True

    def explore(self):
        self.last_msdp_from_log()
        self.look()
        if not self.cur:
            sys.exit("нет данных MSDP: бот запущен со старым кодом?")
        area = self.cur["area"]
        start = self.cur["vnum"]
        self.walked = {}                          # vnum -> {направление: vnum, куда реально пришли}
        tried = set()
        old = os.path.join(OUT, re.sub(r"[^\w]+", "_", area).strip("_") + ".json")
        if os.path.exists(old):                   # известные ДТ («dt»: {направление: что там}) не трогаем
            self.known_dt = {v: set(r.get("dt", {})) for v, r in
                             json.load(open(old, encoding="utf-8"))["rooms"].items() if r.get("dt")}
        saved = 0
        while True:
            self.safe()
            if len(self.rooms) >= saved + 10:         # сохраняемся по ходу: погибнем — карта не пропадёт
                self.save(area, start)
                saved = len(self.rooms)
            node = self.record()
            self.inspect_mobs(node)
            v = self.cur["vnum"]
            todo = self.todo(v, tried)
            if node["dt_hint"]:
                node["skipped_dt"] = [d for d in node["exits"] if self.rooms.get(node["exits"][d]) is None]
            if todo:
                d = todo[0]
                tried.add((v, d))
                if not self.step(d):
                    if self.bot.status and self.bot.status.in_battle:   # шаг сорвал бой, а не стена: добить и повторить
                        tried.discard((v, d))
                        self.bad.discard((v, d))
                        self.safe()
                        continue
                    node.setdefault("blocked", []).append(d)
                    continue
                if self.cur["area"] != area:           # вышли в другую зону: назад
                    node.setdefault("borders", {})[d] = self.cur["area"]
                    self.walked[v].pop(d, None)
                    self.move(BACK[d])
                continue
            path = self.path_to_todo(tried)
            if not path:
                break
            for d in path:                              # если пришли не туда, на следующем круге план пересчитается
                v = self.cur["vnum"]
                expected = self.walked.get(v, {}).get(d) or self.rooms[v]["exits"].get(d)
                if not self.step(d) or self.cur["vnum"] != expected:
                    if self.bot.status and self.bot.status.in_battle:
                        self.bad.discard((v, d))
                        self.safe()
                    break
                self.record()
        return area, start

    def save(self, area, start):
        os.makedirs(OUT, exist_ok=True)
        slug = re.sub(r"[^\w]+", "_", area).strip("_")
        base = os.path.join(OUT, slug)
        if os.path.exists(base + ".json"):         # повторное изучение дополняет старое (убитых мобов уже нет)
            old = json.load(open(base + ".json", encoding="utf-8"))
            self.mobs = {**old.get("mobs", {}), **self.mobs}
            for v, r in old.get("rooms", {}).items():   # пометки ДТ, записанные вручную, не теряем
                if r.get("dt") and v in self.rooms:
                    self.rooms[v].setdefault("dt", r["dt"])
            self.rooms = {**old.get("rooms", {}), **self.rooms}
        json.dump({"area": area, "start": start, "rooms": self.rooms, "mobs": self.mobs},
                  open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(base + "_mobs.csv", "w", encoding="cp1251", newline="", errors="replace") as f:
            w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
            w.writerow(["Имя моба", "Слово", "Мобы в комнате", "MaxHp", "Уровень", "Профессия", "Раса", "Флаги",
                        "Навыки", "Комната", "vnum"])
            for m in self.mobs.values():
                w.writerow([m.get("name", ""), m.get("word", ""), m["look"], m.get("hp", ""), m.get("level", ""),
                            m.get("prof", ""), m.get("race", ""), m.get("flags", ""), m.get("skills", ""),
                            m["room"], m["vnum"]])
        open(base + "_map.txt", "w", encoding="utf-8").write(draw(self.rooms, start))
        return base


def draw(rooms, start):
    pos, todo = {start: (0, 0, 0)}, [start]
    while todo:
        v = todo.pop()
        x, y, z = pos[v]
        for d, t in rooms[v]["exits"].items():
            if t in rooms and t not in pos and d in VEC:
                dx, dy, dz = VEC[d]
                pos[t] = (x + dx, y + dy, z + dz)
                todo.append(t)
    out = []
    for z in sorted({p[2] for p in pos.values()}, reverse=True):
        cells = {(x, y): v for v, (x, y, zz) in pos.items() if zz == z}
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        out.append(f"=== уровень {z} ===")
        for y in range(min(ys), max(ys) + 1):
            row, low = "", ""
            for x in range(min(xs), max(xs) + 1):
                v = cells.get((x, y))
                if not v:
                    row, low = row + "    ", low + "    "
                    continue
                r = rooms[v]
                mark = "S" if v == start else "!" if r.get("dt_hint") else "?" if r["hidden"] else \
                       "m" if r["mobs"] else "^" if "U" in r["exits"] else "v" if "D" in r["exits"] else "#"
                row += f"[{mark}]" + ("-" if "E" in r["exits"] else " ")
                low += (" | " if "S" in r["exits"] else "   ") + " "
            out.append(row.rstrip())
            out.append(low.rstrip())
    out.append("S вход  m мобы  ? скрытый выход  ! подсказка ловушки  ^/v вверх/вниз")
    return "\n".join(out)


if __name__ == "__main__":
    ex = Explorer()
    area, start = ex.explore()
    base = ex.save(area, start)
    rooms = ex.rooms
    print(f"зона «{area}»: комнат {len(rooms)}, мобов {len(ex.mobs)}")
    print("скрытые выходы:", [(r["name"], r["hidden"]) for r in rooms.values() if r["hidden"]])
    print("подсказки ловушек:", [(r["name"], r.get("skipped_dt")) for r in rooms.values() if r.get("dt_hint")])
    print("границы:", [(r["name"], r.get("borders")) for r in rooms.values() if r.get("borders")])
    print("не пройти:", [(v, r["name"], r["blocked"]) for v, r in rooms.items() if r.get("blocked")])
    print("ведут не туда:", [(v, r["name"], r["tricky"]) for v, r in rooms.items() if r.get("tricky")])
    print(open(base + "_map.txt", encoding="utf-8").read())
    for m in sorted(ex.mobs.values(), key=lambda m: int(m.get("level", 0) or 0)):
        print(f"  {m.get('level', '?'):>3} {m.get('name') or m['look']} [{m.get('word') or '?'}] | {m.get('prof', '')}"
              f" | {m.get('flags', '')} | {m['room']}")
