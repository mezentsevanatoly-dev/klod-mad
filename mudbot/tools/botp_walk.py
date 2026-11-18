"""Пройти зону по маршруту JMC-бота Чвырла (.botp): шаги «#if {$MsdpRoomVnum ==X} {подкр север;бгр}».

python tools/botp_walk.py <файл.botp> <mob.csv> [с_шага] [до_шага]
В каждой комнате маршрута бьёт мобов из mob.csv: 2+ врага и нет никого постороннего -> землетрясение (друид),
потом по одному «убить <слово>». На строках «.триг ...» (квестовые действия, ожидания) останавливается и печатает
номер шага — дальше вручную и запуск «с_шага». Останов и при уходе с маршрута, смерти, HP < 40%.
"""
import csv
import re
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from explore_msdp import CMD, Explorer  # noqa: E402

QUAKE = "колд землетрясение"   # масс друида: бьёт всех в клетке, кроме согруппников
RU = {v: k for k, v in CMD.items()}
ALLIES = ("зорон", "тадия", "айлина", "мряка", "штыра", "олирон", "кейб", "съезо", "карис", "сьерон")
# согруппники и мы сами в списке комнаты — не цели; к этому списку Walker добавляет имена из `пгр` (в группе не только Зорон)
QUAFF = "осуш фля.раз"           # фляга разрушителя заклинаний = развеять магию на себя (работает и в облике зверя)
CASTERS = {"Лекарь", "Маг", "Некромант", "Друид", "Паладин", "Рыцарь смерти"}
FELL_RE = re.compile(r"^(.+?) упал[аио]? и больно ударил")       # сбит землетрясением -> сидит/лежит
HEAL_RE = re.compile(r"^(.+?) произнес\S* магические слова '(массовое )?исцеление'")


def norm(s):
    """«Каменный тролль ... стоит тут. (невидим) ...огненный щит» -> «каменный тролль ... стоит тут.»"""
    s = re.sub(r"\s*\.\.\..*$", "", s)
    s = re.sub(r"\s*\((невидим|летит|очарован|спрятал)\w*\)", "", s)
    return s.strip().rstrip(".").lower()            # «...замер тут ...аура» — точки перед аурой нет


def load_steps(path):
    lines = open(path, encoding="cp1251").read().splitlines()
    start = next(i for i, l in enumerate(lines)                 # после создания области
                 if "SumReset 0" in l or "BotInZone = true" in l)
    steps = []
    if "MsdpRoomVnum ==" in lines[start]:                   # «505034 восток;BotInZone = true» — уже шаг маршрута
        start -= 1
    for l in lines[start + 1:]:
        m = re.search(r"\$MsdpRoomVnum ==\s*(\d+)\} \{([^}]*)\}", l)
        if m:
            steps.append(("step", m.group(1), m.group(2)))
        elif l.strip():
            steps.append(("trig", l.strip(), ""))
    return steps


def load_mobs(path):
    mobs = {}
    with open(path, encoding="cp1251") as f:
        for row in csv.DictReader(f, delimiter=";"):
            mobs[norm(row["Описание в комнате"])] = {"name": row["Имя моба"], "level": row["Уровень"],
                                                    "word": row["Имя моба"].split()[0].lower(),
                                                    # из csv Чвырлы берём ТОЛЬКО флаг «Мирный» (остальное там кривое — польз.)
                                                    "peace": "Мирный" in row["Флаги NPC"]}
    return mobs


def load_casters():
    """Имена мобов-кастеров (нижний регистр): профессии из СВОИХ файлов зон areas/msdp/*.json + те, кто кастовал в логах
    (out.log). csv Чвырлы не используем."""
    import glob
    import json
    import os
    names = set()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in glob.glob(os.path.join(here, "areas", "msdp", "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for m in (d.get("mobs") or {}).values():
            if m.get("name") and m.get("prof") in CASTERS:
                names.add(m["name"].lower())
    cast_re = re.compile(r"^(.+?) произнес\S* магические слова '")
    try:
        with open(os.path.join(here, "out.log"), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = cast_re.match(line)
                if m and not m.group(1).startswith(("Вы", "Отринувший") + tuple(a.capitalize() for a in ALLIES)):
                    names.add(m.group(1).lower())
    except OSError:
        pass
    return names


KP_RE = re.compile(r"(\S+) начал[аио]? медленно превращаться в камень")      # «Зорон начал медленно превращаться в камень»
ME = "Тадия"
DOWN = ("Сидит", "Лежит")
ARRIVE_RE = re.compile(r"\b(пришел|пришла|пришло|пришли|прибежал\w*|прилетел\w*|приполз\w*|появил\w*|выскочил\w*)\b")
CD_RE = re.compile(r"Вы (?:вновь|снова) можете использовать (заклинание|умение) '([^']+)'")


class Walker(Explorer):
    def __init__(self, mobs):
        super().__init__()
        self.known = mobs
        self.casters = load_casters()                 # кто кастует: свои файлы зон + логи
        self.boss_fight = False                      # ласт: полиморф разрешён (storm_heart.py ставит True)
        self.arrived = False                          # кто-то (не свой) вошёл в клетку — не ждать, пока сагрит: осмотреть и бить
        self.kp_t = {}
        self.cd = {}                                  # откаты: имя -> True (готово) / False (ждём сообщения игры)
        self._cd_seen = len(self.bot.history)

    def pump(self, sec):
        got = super().pump(sec)
        h = self.bot.history
        for l in h[self._cd_seen:]:                   # «Вы вновь можете использовать заклинание 'регенерация'.»
            if ARRIVE_RE.search(l) and not any(a in l.lower() for a in ALLIES) and " с " in l:
                self.arrived = True                   # «Гоблин пришёл с севера.» (мобы из csv ударим первыми)
            m = CD_RE.search(l)
            if m:
                self.cd[m.group(2).lower()] = True
            k = KP_RE.search(l)
            if k and k.group(1) not in ("Вы", ME) and time.time() - self.kp_t.get(k.group(1), 0) > 20:
                self.kp_t[k.group(1)] = time.time()          # у другого КП: зач зак.кам <имя> (польз.)
                self.c.send(f"зач зак.кам {k.group(1)}")
                print(f"  КП у {k.group(1)}: зач зак.кам {k.group(1)}", flush=True)
        self._cd_seen = len(h)
        return got

    def cast_cd(self, name, cmd):
        """Каст с откатом: если игра ещё не написала «можете использовать» — не пытаться. Результат запоминаем."""
        if self.cd.get(name) is False:
            return False
        out = self.answer(cmd, 1.6)
        if any("пока не можете" in l for l in out):
            self.cd[name] = False
            return False
        if any(f"'{name}'" in l and "произнесли" in l for l in out):
            self.cd[name] = False                     # ушёл — до сообщения об окончании отката не повторять
            return True
        return False

    def is_caster(self, name):
        n = name.lower()
        return n in self.casters or any(n.endswith(c) or c.endswith(n) for c in self.casters if len(c) > 5)

    def look(self):
        self.send("смотреть краткий", 1.0)           # без описания комнаты (меньше спама), мобы и выходы те же

    def speedwalk(self, path, expect=None, chunk=12):
        """Спидволк: путь вида «2ws3w5n» уходит в игру пачками «с;с;в;ю...» без пауз на шаг (польз.).
        expect — vnum, где должны оказаться; не дошли (дверь, бой) — добиваем обычным goto по картам."""
        import re as _re
        words = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
        steps = [words[d] for n, d in _re.findall(r"(\d*)([nsewud])", path) for _ in range(int(n or 1))]
        for i in range(0, len(steps), chunk):
            self.c.send(";".join(steps[i:i + chunk]))
        last, quiet = None, 0.0
        t0 = time.time()
        while time.time() - t0 < 25 + len(steps) * 1.0:       # ждём, пока комнаты перестанут меняться (очередь игры медленнее)
            self.pump(0.3)
            if self.cur and self.cur["vnum"] == last:
                quiet += 0.3
            else:
                last, quiet = self.cur["vnum"] if self.cur else None, 0.0
            if (expect and last == expect and quiet >= 0.6) or quiet >= 7.0:
                break
        if expect and self.cur["vnum"] != expect:
            from goto import goto
            goto(self, expect)
        return not expect or self.cur["vnum"] == expect

    def move(self, d):
        """Шаг с подкрадыванием (подкр): мобы не замечают входа, первым бьёт землетрясение."""
        before = self.cur["vnum"]
        self.c.send("подкр " + CMD[d])
        t0 = time.time()
        while time.time() - t0 < 10:
            self.pump(0.3)
            if self.cur["vnum"] != before:
                self.pump(0.5)                   # дочитать комнату: classify возьмёт её без «смотреть»
                self.fresh = True
                return True
        self.last_msdp_from_log()                # MSDP мог прийти мимо очереди
        if self.cur["vnum"] != before:
            return True
        return super().move(d)                   # не вышло (сторож, дверь) — обычный шаг explore_msdp

    def classify(self):
        if not getattr(self, "fresh", False) or self.arrived:
            self.look()
        self.fresh = False
        self.arrived = False
        r = self.last_room
        foes, other = [], []           # в своём экземпляре чужих нет: враг — всякий моб, кроме известных мирных
        try:
            import zone_journal as zj
            zj.mobs(self, [l for l in (r.mobs if r else []) if not any(a in norm(l) for a in self.allies())])
        except Exception:
            pass
        for line in (r.mobs if r else []):
            s = norm(line)
            if line.startswith("Труп") or s.endswith("лежит тут"):
                continue
            if any(a in s for a in self.allies()):   # согруппники — не враги
                continue
            if "бесплотн" in s:                      # тени Мории: забить, Зорон идёт первым (польз.)
                continue
            m = self.known.get(s) or next((x for x in self.known.values()
                                           if s.startswith(x["name"].lower() + " ")), None)
            if m and m["peace"]:
                other.append(m["name"])
            elif m or re.search(r"\b(тут|здесь|с вами!?)$", s) or "сражается с" in s:    # в т.ч. «сражается с Зороном!»
                foes.append(m or {"name": line, "level": "?", "word": s.split()[0]})
            # прочее — строки боя, перемешанные с осмотром
        st = self.bot.status
        if not foes and st and st.in_battle:   # бой идёт, а в списке пусто (невидимка, строки боя) — враг есть
            foes.append({"name": st.foe or "?", "level": "?", "word": (st.foe or "?").split()[-1]})
        return foes, other

    # (подстрока строки команды `аф` в нижнем регистре, действие). Порядок = приоритет (польз.):
    # УД, забвение, молчание, морф, проклятие, яд, слепота; потом кровотечение, оковы тьмы, замедление, слабоумие
    AFF_RULES = [
        ("украсть душу", "осушить освобождения"),
        ("забвени", QUAFF),
        ("молчани", "перевязка"), ("безмолви", "перевязка"),
        ("полиморф", QUAFF), ("звериный облик", QUAFF),
        ("проклят", "колд об.очищ"),
        ("яд:", "колд сл.жиз"), ("болезн", "колд сл.жиз"),
        ("потемнени", "колд сл.свет"), ("слепот", "колд сл.свет"),
        ("кровотечени", "колд крит.исц"),
        ("оковы тьмы", "колд разв.маг я"), ("медлительн", "колд разв.маг я"), ("скованн", "колд разв.маг я"),
        ("паралич", "колд разв.маг я"),
        ("слабоуми", "колд осв.разу"), ("слабост", "колд осв.разу"),
    ]

    def aff(self):
        """Одна команда `аф` (польз.): строки аффектов. Не спамить — один вызов на проход."""
        return [l.rstrip() for l in self.answer("аф", 1.0) if l.startswith("   ")]

    def staff_left(self, lines):
        """Секунд до конца заряда посоха по `аф` («магический посох: земля  21:05»); 0 — нет заряда."""
        for l in lines:
            m = re.search(r"магический посох.*?(\d+):(\d+)\s*$", l)
            if m:
                return int(m.group(1)) * 60 + int(m.group(2))
        return 0

    def cure(self, lines=None):
        """Снять эффекты по `аф` в порядке приоритета; забвение/морф — фляга снимает и молчание заодно."""
        lines = self.aff() if lines is None else lines
        low = [l.lower() for l in lines]
        acts = []
        for key, act in self.AFF_RULES:
            if any(key in l for l in low) and act not in acts:
                acts.append(act)
        if QUAFF in acts and "перевязка" in acts:
            acts.remove("перевязка")                 # фляга (развеять магию) уже снимает молчание
        for a in acts:
            n = 3 if a == "колд крит.исц" else 1
            for _ in range(n):
                out = self.answer(a, 1.6)
                if a.startswith("колд") and any("не знаете такого" in l for l in out):
                    out = self.answer(QUAFF, 1.6)    # забвение стёрло заклинание — фляга
                print(f"  снимаю: {a}: " + " | ".join(l.strip() for l in out if l.strip())[:140], flush=True)
        return lines, acts

    def charge_staff(self):
        if getattr(self, "no_roses", False):
            return False
        ok = False
        for c in ("сня 18.", "од роза", "посох", "од все"):       # польз.: 18. — левая рука
            out = self.answer(c, 1.2)
            if c == "посох":
                ok = any("зарядили" in l for l in out)
        if ok:
            print("  посох заряжен", flush=True)
        else:                                                      # роз нет (польз.: кончились) — больше не пытаться
            self.no_roses = True
            print("  посох НЕ заряжен: нет роз (больше не пытаюсь)", flush=True)
        return ok

    def blind(self):
        """Слепа: последняя комната в тексте «Здесь темно...» или недавно «Вы ослепли!» без «Вы прозрели!»."""
        h = self.bot.history[-60:]
        state = False
        for l in h:
            if "Вы ослепли" in l or l.strip() == "Здесь темно...":
                state = True
            elif "Вы прозрели" in l:
                state = False
        return state

    def allies(self):
        """Согруппники: фиксированный список + имена из последней таблицы группы (польз.: в группе не только Зорон)."""
        return ALLIES + tuple(getattr(self, "_allies", ()))

    def group_state(self):
        """Таблица группы: {имя: {'Позиция': 'Стоит', 'Рядом': 'Д', 'Холд': 'Н', ...}} одной командой `пгр`."""
        out = self.answer("пгр позиц ряд холд молч слеп прокл полим забв укр", 1.2)
        head = next((l.split()[1:] for l in out if l.strip().startswith("Имя")), None)
        rows = {}
        for l in out:
            p = l.split()
            if p and p[0].isdigit():                       # после `груп номер …` строки начинаются с номера (польз.) — отбросить
                p = p[1:]
            if head and len(p) == len(head) + 1 and p[0] != "Имя" and not l.strip().startswith("-") and not p[0][0].isdigit():
                rows[p[0]] = dict(zip(head, p[1:]))
        if rows:
            self._allies = tuple(n.lower() for n in rows)
        return rows

    def to_group(self, cmds, gap=0.4):
        for c in cmds:
            self.c.send(c)
            self.pump(gap)

    def summon_via_karis(self, rows):
        """Есть отставшие и в группе Карис (польз.: себя призвать она не может, кого-то Тадия не призовёт —
        Съезо, Кейб) -> `гг !очистить; гг !сумм`. True — призыв отдан группе, поодиночке не зовём."""
        far = [n for n, r in rows.items() if n != ME and r.get("Рядом") == "Н"]
        if not far or not any(n.lower() == "карис" for n in rows) or "Карис" in far:
            return False
        self.to_group(["гг !очистить", "гг !сумм"])
        print(f"  группа: {', '.join(far)} отстали — гг !очистить; гг !сумм (Карис)", flush=True)
        return True

    def check_group(self):
        """После боя (польз.): сидит кто-то — гг !очистить; гг !встать; гг !од все и ждём, пока встанет; отставшего —
        к призыв <имя>; холд/забвение — снять; УД у другого — ему в приват. КП ловит pump (срочно)."""
        rows = self.group_state()
        others = {n: r for n, r in rows.items() if n != ME}
        if any(r.get("Позиция") in DOWN for r in others.values()):
            self.to_group(["гг !очистить", "гг !встать", "гг !од все"])
            for _ in range(6):                                    # ждём, пока встанет
                self.pump(2.0)
                others = {n: r for n, r in self.group_state().items() if n != ME}
                if not any(r.get("Позиция") in DOWN for r in others.values()):
                    break
            print("  группа: подняла сидящих" if not any(r.get("Позиция") in DOWN for r in others.values())
                  else "  группа: кто-то всё ещё сидит", flush=True)
        via_karis = self.summon_via_karis(rows)
        for n, r in others.items():
            nm = n.lower()
            if r.get("Рядом") == "Н":
                if not via_karis:
                    self.answer(f"к призыв {nm}", 1.6)
                    print(f"  группа: {n} отстал — к призыв {nm}", flush=True)
                continue
            if r.get("Укр") not in ("Н", None):
                self.to_group([f"ск {nm} !очистить", f"ск {nm} !осуш осв."])
                print(f"  группа: УД у {n} — ск {nm} !осуш осв.", flush=True)
            if r.get("Холд") not in ("Н", None):
                self.answer(f"к осв.разу {nm}", 1.6)
                print(f"  группа: холд у {n} — к осв.разу {nm}", flush=True)
            if r.get("Забв") not in ("Н", None):
                self.answer(f"к разв.маг {nm}", 1.6)
                print(f"  группа: забвение у {n} — к разв.маг {nm}", flush=True)
        return others

    def relax(self):
        """Расслаб группой (польз.): гг !отд, гг !расслаб, себе отд/расслаб, сразу вст и гг !вст -> «прилив сил» (+HP, ~10 мин).
        Откат 12 мин; если игра ещё не написала «Вы вновь можете использовать умение 'расслабиться'» — не пытаться."""
        if self.cd.get("расслабиться") is False:
            return False
        self.to_group(["гг !отд", "гг !расслаб"], gap=0.3)
        self.answer("отдыхать", 0.8)
        out = self.answer("расслабиться", 1.2)
        ok = any("расслабились" in l for l in out)
        self.answer("вст", 0.8)
        self.to_group(["гг !вст"], gap=0.3)
        if ok or any("пока не можете" in l for l in out):
            self.cd["расслабиться"] = False
        print("  расслаб " + ("сделан" if ok else "не прошёл (откат)"), flush=True)
        return ok

    def maintain(self, lines=None):
        """Раз в ~90 с вне боя: ОДИН `аф` -> посох, регенерация, прилив сил (расслаб), группа. Не спамить."""
        if time.time() - getattr(self, "_maint_t", 0) < 90:
            return
        self._maint_t = time.time()
        st = self.bot.status
        if st and st.in_battle:
            return
        lines = self.aff() if lines is None else lines
        if self.staff_left(lines) < 120:
            self.charge_staff()
        if not any(re.match(r"\s*регенерация:", l.lower()) for l in lines):
            self.cast_cd("регенерация", "колд регенерация")
        if not any("прилив сил" in l.lower() for l in lines):      # баф расслаба пропал (польз.): ПрСил = Н -> расслаб
            self.relax()

    def recover(self):
        """После боя: ОДИН `аф` -> снять эффекты, проверить заряд посоха, подлечиться перевязкой."""
        lines, acts = self.cure()
        self.check_group()
        left = self.staff_left(lines)
        if left < 120:                                # как у Чвырлы: посох меньше ~2 мин — перезарядить
            self.charge_staff()
        # заклинание в `аф` — «регенерация: степень 10 [10] 30:04» (а «быстрая регенерация [6]» — постоянный эффект шмота)
        if not any(re.match(r"\s*регенерация:", l.lower()) for l in lines):    # свеяли/кончилась; откат 6 мин — кастуем,
            if self.cast_cd("регенерация", "колд регенерация"):   # когда игра написала «вновь можете…»
                print("  регенерация перекастована", flush=True)
        if not any("прилив сил" in l.lower() for l in lines):
            self.relax()
        st = self.bot.status
        if st and st.hp < 0.6 * self.bot.max_hp and not any("перевязка" in a for a in acts):
            out = self.answer("перевязка", 2.0)       # урон в основном держит щит маны; HP — перевязкой
            print(f"  перевязка: HP {st.hp}/{self.bot.max_hp}", flush=True)

    def pierce_heart(self):
        """Черное сердце бури исцеляется от смертельной раны: луч древнего света (дал дух святыни) в руку
        и «пронзить сердце бури», пока не умрёт; потом снова коса."""
        # пронзить можно только при малом HP сердца — это и есть момент «исцеляется от смертельной раны»
        print("  сердце бури исцелилось: луч вместо посоха, пронзаю", flush=True)
        self.answer("сменить коса,луч.древ.света", 1.2)      # как у Чвырлы: «сменить <оружие>,луч.древ.света»
        for _ in range(5):
            out = self.answer("пронзить сердце бури", 1.5)
            print("    " + " | ".join(l.strip() for l in out if l.strip())[:200], flush=True)
            if any("Черное сердце бури мертв" in l for l in self.bot.history[-60:]):
                break
        self.answer("сменить луч.древ.света,коса", 1.5)     # снова посох (пламенная коса)

    def fight_here(self):
        fought = False
        heal_seen = set()
        for _ in range(30):
            foes, other = self.classify()
            if not foes:
                # из клетки не уходить, пока группа бьёт моба; квест засчитывается всем в клетке (польз.)
                self.pump(2.0)
                foes, other = self.classify()
                if foes:
                    continue
                if fought:                           # был бой
                    self.recover()
                    # после боя (польз.): не выбило ли у кого оружие масс. слабостью — смотрим клетку и подбираем
                    self.look()
                    r = self.last_room
                    floor = [o for o in (r.objects if r else []) if "лежит" in o and "монет" not in o]
                    if floor:
                        print(f"  после боя на полу: {floor[:4]}", flush=True)
                        self.answer("взять все", 1.0)
                        self.answer("од все", 1.0)
                return True
            for l in (self.last_room.mobs if self.last_room else []):      # холд у согруппника — снять СРАЗУ (польз.)
                who = next((a for a in self.allies() if a not in ("тадия", "айлина") and a in l.lower()), None) \
                    if "обездвижен" in l else None
                if who:
                    self.c.send(f"к осв.разу {who}")
                    print(f"  холд у {who}: к осв.разу {who}", flush=True)
                    self.pump(1.2)
                    break
            if time.time() - getattr(self, "_ally_t", 0) > 5:     # забвение/холд у согруппника — снимать прямо в бою (польз.)
                self._ally_t = time.time()
                for n, r in self.group_state().items():
                    if n == ME or r.get("Рядом") == "Н":
                        continue
                    nm = n.lower()
                    if r.get("Забв") not in ("Н", None):
                        self.c.send(f"к разв.маг {nm}")
                        print(f"  забвение у {n}: к разв.маг {nm}", flush=True)
                        self.pump(1.0)
                    elif r.get("Холд") not in ("Н", None):
                        self.c.send(f"к осв.разу {nm}")
                        print(f"  холд у {n}: к осв.разу {nm}", flush=True)
                        self.pump(1.0)
            if self.blind():                  # ослепла: сначала слово света (иначе кастую вслепую)
                for c in ("очистить", "вст", "колд сл.свет"):
                    self.c.send(c)
                    self.pump(0.4)
                print("  слепота: колд сл.свет", flush=True)
                continue
            if not other:                     # всегда землетрясение, пока в клетке только враги
                n0 = len(self.bot.history)
                if len(getattr(self, "_allies", ())) >= 3:      # польз.: в группе 3+ — группа бьёт сама, я слежу и снимаю дебаффы;
                    self.c.send("гг !фраг")                      # землетрясение — только если после «!фраг» остались живые
                    self.pump(2.5)
                    st = self.bot.status
                    if not (st and st.in_battle):
                        fought = True
                        print("  группа добила сама (гг !фраг), землетрясение не нужно", flush=True)
                        continue
                    print("  после «!фраг» остались живые — землетрясение", flush=True)
                else:
                    for c in ("гг !фраг", "гг !фраг"):      # польз.: перед землетрясением группе «!фраг» дважды
                        self.c.send(c)
                self.send(QUAKE, 2.5)
                out = self.bot.history[n0:]
                xp = sum(int(m.group(1)) for l in out if (m := re.match(r"^Вы получили (\d+) един", l)))
                dead = [l for l in out if l.endswith("мертв. R.I.P.") or l.endswith("мертва. R.I.P.")]
                print(f"  землетрясение: врагов {len(foes)}, убито {len(dead)}, опыт {xp}", flush=True)
                fought = True
                if any("мгновенно исцеляется от смертельной раны" in l for l in out):
                    self.pierce_heart()                  # Пустоши троллей: сердце бури убивает только луч духа
                if not any("магические слова 'землетрясение'" in l for l in out):
                    # каст не ушёл: сбили, оглушили, холд, молчание — очередь забита (польз.): очистить; вст; действие
                    silent = any("произнести ни слова" in l or "выговорить" in l or "способность разговаривать" in l
                                 for l in out)
                    if silent or any("Вы замерли" in l or "не в силах шевельнуться" in l for l in out):
                        self.cure()                      # молчание/холд — снять по таблице группы
                    else:
                        for c in ("очистить", "вст", QUAKE):
                            self.c.send(c)
                        self.pump(2.0)
                    print("  каст не ушёл: очистить; вст; " + ("снять" if silent else "землетрясение"), flush=True)
                # лекари («X произнес 'исцеление'») — полиморф (на мобов без астрального/магического щита)
                healers = [m.group(1) for l in out if (m := HEAL_RE.match(l))]
                heal_seen.update(h.lower() for h in healers)               # кто реально лечит в этом бою (csv Мории пуст)
                n_healers = len(heal_seen)
                # полиморф — только на ластах или когда хилов в клетке больше 2 (польз.: у морфа долгий кд)
                if healers and (self.boss_fight or n_healers > 2) and time.time() - getattr(self, "morph_t", 0) > 60:
                    words = " ".join(h.split()[0].lower()[:5] for h in dict.fromkeys(healers))
                    out3 = self.answer(f"колд полиморф {words}", 2.0)
                    self.morph_t = time.time()
                    print(f"  полиморф на лекарей {words}: " + " | ".join(
                        l for l in out3 if "хлопок" in l or "не можете" in l or "отраз" in l)[:200], flush=True)
                # живые корни держат сидящих/лежащих (откат 30с–4мин) — только на сбитых с ног лекарей и кастеров
                healers = {h.lower() for h in healers}
                fell = [m.group(1) for l in out if (m := FELL_RE.match(l))]
                casters = [n for n in fell if n.lower() in healers or self.is_caster(n)]
                if casters:
                    out2 = self.answer("колд жив.корн", 1.5)
                    print(f"  живые корни на {', '.join(casters)}: "
                          + (next((l for l in out2 if l.strip()), "") or "?"), flush=True)
                if any(("Вы не можете" in l and "заклинани" not in l) or "Вы не знаете" in l or "Хмм" in l
                       or "не в состоянии" in l for l in out):     # каст не ушёл: молчание/забвение/полиморф
                    print("  каст не прошёл: " + "; ".join(out[-3:]), flush=True)
                    self.recover()
                if self.bot.dead:
                    sys.exit("ПОГИБЛА")
                st = self.bot.status
                if st and st.hp < 0.4 * self.bot.max_hp:
                    sys.exit(f"HP {st.hp}/{self.bot.max_hp}: стоп")
                continue
            print(f"  рядом не цели: {other}", flush=True)
            mob = foes[0]
            n0 = self.bot.history.__len__()
            won = self.bot.kill(mob["word"], timeout=60)
            xp = sum(int(m.group(1)) for l in self.bot.history[n0:] if (m := re.match(r"^Вы получили (\d+) един", l)))
            print(f"  {mob['name']} ({mob['level']}): {'убит' if won else 'НЕ убит'}, опыт {xp}", flush=True)
            if self.bot.dead:
                sys.exit("ПОГИБЛА")
            st = self.bot.status
            if st and st.hp < 0.4 * self.bot.max_hp:
                sys.exit(f"HP {st.hp}/{self.bot.max_hp}: стоп")
            if not won:
                return False
        return True


def walk(w, steps, i, stop):
    """Идти по шагам маршрута [i, stop); возвращает индекс шага, на котором остановилась (== stop — прошла до конца)."""
    while i < min(stop, len(steps)):
        kind, a, cmd = steps[i]
        if kind == "trig":
            if "9999" in a or "войт;" in a:          # дальше дорога домой (спидволк, извозчик) — не наша
                print(f"[{i}] зона пройдена, дальше дорога домой: {a}", flush=True)
                return i
            for c in a.replace(".триг", "").split(";"):
                c = c.strip()
                if not c or (c.startswith(("#", "ждать", "гг", "бгр", "прыг", "пну")) and not c.startswith("гг !")):   # пну — умение файтеров (Чвырла ДК); «гг !…» — наши команды группе
                    continue
                d = c.replace("подкр ", "")
                if d in RU:                              # «подкр юг» после квеста — просто шаг
                    w.fight_here()
                    w.move(RU[d])
                    print(f"[{i}] -> {d} -> {w.cur['vnum']} {w.cur['name']}", flush=True)
                    continue
                out = w.answer(c, 1.5)
                print(f"[{i}] {c}: " + " | ".join(l.strip() for l in out if l.strip())[:300], flush=True)
            i += 1
            continue
        w.maintain()
        if w.cur["vnum"] != a:
            if getattr(w, "plain", False):              # карта старая/чужая: идём по командам Чвырлы, vnum пишем как есть
                print(f"[{i}] vnum {w.cur['vnum']} вместо {a} ({w.cur['name']}) — иду дальше по командам", flush=True)
            else:
                print(f"[{i}] стою в {w.cur['vnum']} {w.cur['name']}, а шаг для {a}: стоп", flush=True)
                return i
        if not w.fight_here():
            print(f"[{i}] бой не закончен: стоп", flush=True)
            return i
        if time.time() - getattr(w, "_near_t", 0) > 5:       # без Зорона из клетки не уходить (польз.): отстал — призвать
            w._near_t = time.time()
            rows = w.group_state()
            if w.summon_via_karis(rows):
                w._near_t = 0
            else:
                for n, r in rows.items():
                    if n != ME and r.get("Рядом") == "Н":
                        w.answer(f"к призыв {n.lower()}", 1.6)
                        print(f"  группа: {n} отстал — к призыв {n.lower()}", flush=True)
                        w._near_t = 0
        # шаг: «взя все;запад», «смастерить помост;брос помост;перебраться», «войти;бгр» — команды по порядку,
        # направление — шаг с подкрадыванием; шаг засчитан, если комната сменилась
        before = w.cur["vnum"]
        for c in cmd.split(";"):
            c = c.strip()
            if not c or (c.startswith(("#", "ждать", "гг", "бгр", "прыг", "пну", "яр ", "толк")) and not c.startswith("гг !")):
                continue
            d = c.replace("подкр ", "").strip()
            if d in RU:
                ok = w.move(RU[d])
                for _ in range(3):                      # сторож «не пускает»: добить и повторить шаг, а не вставать (польз.: без стопов)
                    if ok:
                        break
                    w.fight_here()
                    ok = w.move(RU[d])
                if not ok:
                    print(f"[{i}] {a}: не прошла {d}: стоп", flush=True)
                    return i
                continue
            if c.startswith("кол"):                     # каст из маршрута (полиморф и т.п.) — после входа в комнату
                w.fight_here()
                continue
            out = w.answer(c, 2.5)
            print(f"[{i}] {c}: " + " | ".join(l.strip() for l in out if l.strip())[:200], flush=True)
        stays = not any(c.strip().replace("подкр ", "") in RU or c.strip() in ("войти", "перебраться")
                        for c in cmd.split(";"))      # шаг из одних действий (сундук, г да) — комната та же
        if w.cur["vnum"] == before and not stays:
            print(f"[{i}] {a}: «{cmd}» не сменило комнату: стоп", flush=True)
            return i
        print(f"[{i}] {a} -> {cmd} -> {w.cur['vnum']} {w.cur['name']}", flush=True)
        try:
            import zone_journal as zj
            zj.step(w, i, a, cmd)
        except Exception:
            pass
        i += 1
    print("маршрут пройден")
    return i


def main():
    steps = load_steps(sys.argv[1])
    w = Walker(load_mobs(sys.argv[2]))
    i = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    stop = int(sys.argv[4]) if len(sys.argv) > 4 else len(steps)    # остановиться перед этим шагом
    w.last_msdp_from_log()
    w.plain = len(sys.argv) > 5 and sys.argv[5] == "plain"          # без проверки vnum (разметка по старой карте)
    import zone_journal as zj
    zj.begin(w)
    end = walk(w, steps, i, stop)
    path = zj.end(w, "дошла до шага %s из %s" % (end, min(stop, len(steps))))
    print(f"журнал: {path}", flush=True)


if __name__ == "__main__":
    main()
