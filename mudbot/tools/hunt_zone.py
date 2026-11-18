"""Охота по изученной зоне (areas/msdp/<зона>.json): обойти комнаты, убить мобов по их словам, собрать стаф.

python tools/hunt_zone.py Парк_аттракционов [макс_уровень]
Мирных ([Мирный]) и выше макс_уровня не трогаем. С трупа: «взять все труп», что выпало, пишем моб -> вещи
в areas/msdp/<зона>_loot.json. Безопасность как у explore_msdp: смерть -> стоп, HP < 50% -> отдых,
в бою Bot.kill сам бежит при HP < 40%.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from explore_msdp import CMD, OUT, Explorer  # noqa: E402

LOOT_RE = re.compile(r"^Вы взяли (.+?) из трупа")
XP_RE = re.compile(r"^Вы получили (\d+) единиц")
ITEMS = os.path.join(OUT, "items.json")                    # стаф всех зон: вещь -> характеристики
GOLD_RE =re.compile(r"^Вы взяли кучку монет из трупа .*?, там был[аио]? (\d+) монет")
# в комнату кто-то вошёл: «Горный козел прискакал с юга.», «...скелет прибежал из Дольмена»
ARRIVE_RE = re.compile(r"\b(при(шел|шла|шло|шли|беж|лет|полз|скака|плы)\w*|появил\w*)\b")
RITUAL = "колд темный.ритуал"     # массовое проклятие ДК: агрит всех в комнате, кроме согруппников


def mob_key(line):
    return re.sub(r"\s+\.\.\..*$", "", line).strip()


class Hunter(Explorer):
    def __init__(self, zone, max_level=99):
        super().__init__()
        d = json.load(open(os.path.join(OUT, zone + ".json"), encoding="utf-8"))
        self.zone, self.rooms, self.mobs, self.max_level = zone, d["rooms"], d["mobs"], max_level
        self.loot_path = os.path.join(OUT, zone + "_loot.json")
        self.loot = json.load(open(self.loot_path, encoding="utf-8")) if os.path.exists(self.loot_path) else {}
        self.total = {"kills": 0, "xp": 0, "gold": 0}
        self.items = json.load(open(ITEMS, encoding="utf-8")) if os.path.exists(ITEMS) else {}

    def examine(self, item):
        """«осмотреть слово1.слово2» по вещи в инвентаре: тип, оценка по профессиям, слот, модификаторы."""
        n0 = len(self.bot.history)
        self.c.send("осмотреть " + ".".join(item.split()[:2]))      # «браслет.фокусника»
        self.pump(1.5)
        lines = [l for l in self.bot.history[n0:] if not l.startswith("<<H")]
        info = {"lines": lines, "zone": self.zone}
        mods, on = [], False
        for i, l in enumerate(lines):
            if l.startswith("Оценка:") and i:
                info["rating"] = dict(zip(lines[i - 1].split(), [x.strip() for x in l[7:].split(",")]))
            elif l.startswith("Вы можете одеть это") or l.startswith("Вы можете взять это"):
                info["slot"] = l
            elif l.startswith("Модификаторы"):
                on = True
            elif on and l.startswith(" ") and not l.startswith("   "):
                mods.append(l.strip())
            elif on:
                on = False
        info["mods"] = mods
        info["summary"] = f"Дк {info.get('rating', {}).get('Дк', '?')}; " + "; ".join(mods)
        return info

    def target(self, line):
        m = self.mobs.get(mob_key(line))
        if not m or not m.get("word") or "Мирный" in m.get("flags", "") or m.get("avoid"):
            return None
        if m.get("level") and int(m["level"]) <= 2:      # 1-2 ур. в зоне 15+ — сюжетный/ловушка (дух озера топит убийцу)
            return None
        if int(m.get("level") or 0) > self.max_level:
            return None
        return m

    def keep_vampirism(self):
        """Вампиризм из эликсира летучей мыши (25 глотков, ~17 мин): спал -> глоток. Проверка не чаще раза в минуту."""
        if time.time() - getattr(self, "vamp_checked", 0) < 60:
            return
        self.vamp_checked = time.time()
        if not any("вампиризм" in l for l in self.answer("аффекты", 1.0)):
            out = self.answer("осушить эликсир.мыши", 1.0)
            print("  вампиризм: " + ("выпит эликсир" if any("глоток" in l for l in out) else "эликсира нет"), flush=True)

    def ritual_safe(self, lines, need=2):
        """Темный ритуал бьёт всех в комнате: только если тут need+ мобов и все — наши цели
        (никаких мирных, продавцов, незнакомых строк — это могут быть игроки)."""
        ok = [l for l in lines if l.rstrip().endswith("сражается с вами!") or self.target(l)]
        cell = self.map_cell()                   # миникарта: M — моб высокого уровня, второй @ — другой игрок
        if "M" in cell or cell.count("@") > 1:
            return False
        return len(lines) >= need and len(ok) == len(lines)

    def ritual(self):
        out = self.answer(RITUAL, 1.0)
        print("  темный ритуал: " + (next((l for l in out if l.strip()), "") or "?"), flush=True)

    def on_fight(self, out):
        """В бою кто-то вошёл -> смотрим комнату, если все враги — ритуал на всех."""
        if any(ARRIVE_RE.search(l) for l in out):
            self.look()
            r = self.last_room
            if r and self.ritual_safe(r.mobs, need=1):
                self.ritual()

    def fight_here(self):
        """Бить мобов комнаты по одному, пока есть кого. 2+ враждебных моба -> сначала темный ритуал."""
        for _ in range(10):
            self.look()
            r = self.last_room
            if not r or not self.cur or r.name != self.cur["name"]:
                return
            mob = next((self.target(l) for l in r.mobs if self.target(l)), None)
            if not mob:
                return
            self.keep_vampirism()
            n0, t0 = len(self.bot.history), time.time()
            if self.ritual_safe(r.mobs):
                self.ritual()
            won = self.bot.kill(mob["word"], on_out=self.on_fight)
            secs = round(time.time() - t0, 1)
            if self.bot.dead:
                sys.exit("ПЕРСОНАЖ ПОГИБ: охота остановлена")
            if not won:
                self.last_msdp_from_log()        # могли убежать в другую комнату
                return
            self.c.send("взять все труп")
            self.pump(1.2)
            out = self.bot.history[n0:]
            got = [m.group(1) for l in out if (m := LOOT_RE.match(l)) and not l.startswith("Вы взяли кучку монет")]
            xp = sum(int(m.group(1)) for l in out if (m := XP_RE.match(l)))
            gold = sum(int(m.group(1)) for l in out if (m := GOLD_RE.match(l)))
            name = mob.get("name") or mob["look"]
            print(f"  убит {name} за {secs} с: опыт {xp}, монет {gold}, {', '.join(got) or 'без вещей'}", flush=True)
            entry = self.loot.setdefault(name, {"kills": 0, "items": {}})
            entry["kills"] += 1
            for k, val in (("xp", xp), ("gold", gold), ("secs", secs)):
                entry[k] = round(entry.get(k, 0) + val, 1)
            for it in got:
                entry["items"][it] = entry["items"].get(it, 0) + 1
                if it not in self.items:
                    self.items[it] = self.examine(it)
                    print(f"    {it}: {self.items[it].get('summary', '')}", flush=True)
                    json.dump(self.items, open(ITEMS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            self.total["xp"] += xp
            self.total["gold"] += gold
            self.total["kills"] += 1
            json.dump(self.loot, open(self.loot_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            self.safe()

    def route(self):
        """Порядок обхода: каждый раз ближайшая непосещённая комната (BFS по выходам MSDP)."""
        seen = set()
        while True:
            v0 = self.cur["vnum"]
            seen.add(v0)
            prev, q, goal = {v0: None}, [v0], None
            while q:
                v = q.pop(0)
                if v not in seen:
                    goal = v
                    break
                for d, t in self.rooms.get(v, {}).get("exits", {}).items():
                    if d in CMD and t in self.rooms and t not in prev:
                        prev[t] = (v, d)
                        q.append(t)
            if not goal:
                return
            seen.add(goal)                        # не дошли — всё равно не зацикливаемся на ней
            path, v = [], goal
            while prev[v]:
                v, d = prev[v]
                path.append(d)
            yield path[::-1]

    def hunt(self):
        self.last_msdp_from_log()
        if not self.cur:
            sys.exit("нет данных MSDP")
        node = self.rooms.setdefault(self.cur["vnum"], {"name": self.cur["name"]})   # стоим в незаписанной комнате
        node["exits"] = {k: str(t) for k, t in self.cur["exits"].items()}
        self.fight_here()
        for path in self.route():
            for d in path:
                if not self.move(d) and not (self.open_door(d) and self.move(d)):
                    break
            self.safe()
            self.fight_here()


if __name__ == "__main__":
    h = Hunter(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 99)
    t0 = time.time()
    h.hunt()
    secs = int(time.time() - t0)
    tot = h.total
    print(f"проход за {secs // 60} мин {secs % 60} с: убито {tot['kills']}, опыт {tot['xp']}, монет {tot['gold']}"
          f" ({tot['xp'] * 3600 // max(secs, 1)} опыта/час)")
    runs = os.path.join(OUT, "runs.tsv")                  # журнал проходов по всем зонам
    new = not os.path.exists(runs)
    with open(runs, "a", encoding="utf-8") as f:
        if new:
            f.write("дата\tзона\tсекунд\tубито\tопыт\tмонет\n")
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{h.zone}\t{secs}\t{tot['kills']}\t{tot['xp']}\t{tot['gold']}\n")
    for name, e in h.loot.items():
        k = e["kills"]
        print(f"  {name} x{k}: опыт {e.get('xp', 0) // k}/шт, монет {e.get('gold', 0) // k}/шт,"
              f" бой {e.get('secs', 0) / k:.0f} с, вещи {e['items']}")
