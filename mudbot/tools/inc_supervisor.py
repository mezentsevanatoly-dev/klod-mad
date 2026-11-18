# -*- coding: utf-8 -*-
"""Надсмотрщик прокачки инкарнации в жабе (JMC БОТ ИНКА). Запуск: python -u tools/inc_supervisor.py [--from ИМЯ_ЗОНЫ]
Ведёт зоны по плану (ПЛАН_прокачки_варвара_1-22.md): .бот старт <зона>, ждёт ZONE_END, чинит застои (look краткий, ворота,
потерянный шаг), перед зоной проверяет уровень по «сч». Команды в игру идут только через tools/jmc.py (окно жабы).
Лог: tools/inc_supervisor.log, стоп: создать файл tools/inc_supervisor.stop."""
import os, re, sys, time, subprocess
os.environ.setdefault("JMC_TARGET", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "JMC БОТ ИНКА"))   # tools/jmc.py бьёт в окно жабы Тадии (по умолчанию)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # ...\Клод мад\mudbot
BASE = os.path.dirname(ROOT)                                   # ...\Клод мад
_JT = os.environ.get("JMC_TARGET") or os.path.join(BASE, "JMC БОТ ИНКА")      # жаба, с которой работаем (Инка/Айлина)
LOG = os.path.join(_JT, "claude_game.log")
OUT = os.path.join(HERE, "inc_supervisor.log")
STOP = os.path.join(HERE, "inc_supervisor.stop")
JMC = os.path.join(HERE, "jmc.py")

# (зона, мин. уровень, команды перед зоной через ;)  — по ПЛАН_прокачки_варвара_1-22.md
PLAN = [
    ("школа", 1, ""), ("гильда5", 5, ""), ("парк", 5, "+сет1;#2 кз :колбы солн"), ("гильда6", 6, ""), ("аллея", 6, ""),
    ("канал", 8, ""), ("болото", 9, ""), ("притон", 11, ""), ("переход_р2", 11, ""), ("склад1", 11, ""),
    ("привы1", 12, ""), ("гильда12", 12, ".бот стоп"), ("леч", 13, ""),
    ("каты1", 14, ""), ("привы2", 15, ""), ("склад2", 15, ""), ("гильда15", 15, ""), ("переход_р1", 16, ""), ("порт", 16, ""), ("переход_р2", 16, ""),
    ("гоблины", 17, ""), ("чайный_домик", 17, ""), ("гильда17", 17, ""),
]
FILLER = ["каты2", "порт", "гоблины", "чайный_домик", "привы2", "склад2"]   # чем добирать опыт, если уровня не хватает


# ---------- оповещение человека о проверке присутствия: он отвечает сам, скрипт НЕ отвечает ----------
import threading, collections
_VOC = None
_alert_t = 0


def _vocab():
    global _VOC
    if _VOC is None:
        cnt = collections.Counter()
        for path in (os.path.join(os.environ.get("JMC_TARGET") or "", "claude_game.log"), LOG):
            try:
                with open(path, "rb") as f:
                    f.seek(0, 2); f.seek(max(0, f.tell() - 3000000))
                    for w in re.findall(r"[а-яё]{3,}", f.read().decode("cp1251", "replace").lower()):
                        cnt[w] += 1
            except OSError:
                pass
        extra = []
        for pat in (os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas", "*_mob.csv"), os.path.join(BASE, "JMC БОТ ИНКА", "areas", "*_mob.csv"), os.path.join(ROOT, "data", "help", "*.txt")):
            import glob
            for fp in glob.glob(pat):
                try:
                    raw = open(fp, "rb").read()
                    txt = raw.decode("utf-8") if fp.endswith(".txt") else raw.decode("cp1251", "replace")
                    extra += re.findall(r"[а-яё]{3,}", txt.lower())
                except OSError:
                    pass
        _VOC = {w for w, c in cnt.items() if c >= 2} | set(extra)
    return _VOC


def gibberish_lines(lines):
    voc = _vocab(); out = []
    for s in lines:
        s = re.sub(r"^\d\d:\d\d:\d\d ", "", s).strip()
        if not re.match(r"^[А-ЯЁ][а-яё]+( [а-яё]+){3,9}\.$", s):
            continue
        ws = re.findall(r"[а-яё]{3,}", s.lower())
        if len(ws) >= 3 and sum(1 for w in ws if w not in voc) / len(ws) >= 0.6:
            out.append(s)
    return out


def alert_user(msg):
    """Всплывающее окно поверх всех окон (в потоке, чтобы не блокировать надсмотрщика)."""
    global _alert_t
    if time.time() - _alert_t < 60:
        return
    _alert_t = time.time()
    say("!!! ВСПЛЫВАЮЩЕЕ ОКНО:", msg)
    threading.Thread(target=lambda: __import__("ctypes").windll.user32.MessageBoxW(0, msg, "МАД: нужен ты", 0x40000 | 0x30), daemon=True).start()

def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def jmc(cmd):
    subprocess.run([sys.executable, "-X", "utf8", JMC, "do", "--force", cmd], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)


def lines_from(pos):
    with open(LOG, "rb") as f:
        f.seek(0, 2); size = f.tell()
        if pos > size:
            pos = 0
        f.seek(pos); data = f.read()
    return size, data.decode("cp1251", "replace").splitlines()


def log_size():
    return os.path.getsize(LOG)


def get_level():
    pos = log_size()
    jmc("сч")
    for _ in range(10):
        time.sleep(1.5)
        _, ls = lines_from(pos)
        for s in ls:
            m = re.search(r"Варвар (\d+) уровня", s)
            if m:
                return int(m.group(1))
    return None


AREAS = os.path.join(_JT, "areas")
COMPANION = os.environ.get("COMPANION")      # имя спутницы (Кимп): если лидер - Айлина, следим за Кимпи
CITY_PREFIX = ("115", "100")        # комнаты городов р2 (Геолант) и р1 (Элендор)
NOT_CITY_ZONES = ("гильда", "переход", "закупка", "ремонт")


def get_vnum():
    pos = log_size(); jmc("#showme {V=$MsdpRoomVnum}"); time.sleep(2.5)
    _, ls = lines_from(pos)
    for s in ls:
        m = re.search(r"\bV=(\d+)", s)
        if m:
            return m.group(1)
    return None


def zone_start_vnum(zone):
    try:
        with open(os.path.join(AREAS, zone + ".botp"), encoding="cp1251") as f:
            for i, ln in enumerate(f):
                m = re.search(r"== (\d+)\}", ln)
                if m:
                    return m.group(1)
                if i > 6:
                    break
    except OSError:
        pass
    return None


def wait_hp(frac=0.9, max_s=420):
    """Ждать на складе, пока здоровье не восстановится до frac (по «сч»)."""
    t0 = time.time()
    while time.time() - t0 < max_s:
        pos = log_size(); jmc("сч"); time.sleep(3)
        _, ls = lines_from(pos)
        for s in ls:
            m = re.search(r"Вы имеете (\d+)\((\d+)\) здоровья", s)
            if m:
                cur, mx = int(m.group(1)), int(m.group(2))
                if cur >= frac * mx:
                    return
                say("жду здоровье %d/%d" % (cur, mx))
        time.sleep(25)

def recover_after_throw(zone, vn=None):
    """Выбросило в город (реж трус 30 / охранный свиток / рекол): .бот стоп, путь склад, при необходимости переход, потом зона заново."""
    jmc(".бот стоп"); time.sleep(2)
    jmc("путь склад"); wait_quiet(8, 6, 120)
    v = vn or get_vnum(); sv = zone_start_vnum(zone)
    say("после «путь склад»: комната", v, "| старт зоны", zone, "=", sv)
    if v and sv and v[:3] != sv[:3]:
        t = "переход_р1" if sv.startswith("100") else "переход_р2"
        say("город не тот - сначала", t); run_zone(t)
    wait_hp()

def run_zone(zone, attach=False):
    """Запустить зону и дождаться ZONE_END. Возвращает 'end' | 'stop' | 'dead'. attach=True: зона уже идёт, не стартовать."""
    pos = log_size()
    pts = None
    try:
        import json as _json, walker as _walker
        _pp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "zone_points.json")
        pts = _json.load(open(_pp, encoding="utf-8")).get(zone) if os.path.exists(_pp) else None
    except Exception as _e:
        say("zone_points не прочитаны:", _e)
    _me = os.path.basename(os.environ.get("JMC_TARGET", "").rstrip("\\/"))
    if pts and not attach:
        say("спидволк А->Б:", pts["A"], "->", pts["B"], "(", zone, ")")
        if not _walker.walk(_me, pts["B"], say=say):
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: ходок не дошёл до входа в зону", zone); return "stop"
        if COMPANION:
            time.sleep(3)
            _pp0 = log_size(); time.sleep(1)
            if not _walker.walk("JMC БОТ ИНКА", pts["B"], say=say):
                say("спутница не дошла до входа - жду"); time.sleep(10)
    if not attach and not zone.startswith("переход"):
        # расходники: по 2 экземпляра каждого (камней 1), добрать из :колбы, нет - купить у алхимика (слова пользователя 13.11)
        try:
            import restock as _rs
            for _f in [os.path.basename(os.environ.get("JMC_TARGET", "").rstrip("\\/"))] + (["JMC БОТ ИНКА"] if COMPANION else []):
                say("расходники:", _f)
                _miss = _rs.restock(_f, say=say)
                if _miss:
                    say("в :колбы нет, иду к алхимику:", _miss); _rs.buy(_f, _miss, say=say, run_zone=(run_zone if _f == os.path.basename(os.environ.get("JMC_TARGET", "").rstrip("\\/")) else None))
        except Exception as _e4:
            say("проверка расходников не удалась:", _e4)
    if not attach:
        # между зонами: если я правила BotCore.js/AreaGuard.js - перезагрузить скрипты (внутри зоны reload сбросил бы бота)
        try:
            _sd = os.path.join(os.path.dirname(os.environ.get("JMC_TARGET", "")) if False else os.environ.get("JMC_TARGET", ""), "scripts")
            _mt = max(os.path.getmtime(os.path.join(_sd, f)) for f in ("BotCore.js", "AreaGuard.js") if os.path.exists(os.path.join(_sd, f)))
            # время последней перезагрузки хранится в файле: при новом запуске круга правки, сделанные после неё, иначе не попадали в жабу
            # (13.11 09:48 бесы прошли старый пустой инст: AreaGuard в памяти был со старым AREA_NOWAIT)
            _rf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reload_at.txt")
            _ra = globals().get("_RELOADED_AT") or (float(open(_rf).read().strip() or 0) if os.path.exists(_rf) else 0)
            if _mt > _ra:
                say("скрипты изменены - #reloadscripts между зонами"); jmc("#reloadscripts"); time.sleep(6)
                globals()["_RELOADED_AT"] = time.time(); open(_rf, "w").write(str(time.time()))
        except Exception as _e:
            say("reload-проверка не удалась:", _e)
        # перед стартом: обе в стартовой клетке зоны (иначе первый шаг ждёт вечно) и Кимпи в группе Айлины (иначе она не посетитель инста)
        try:
            import walker as _wk
            _sv = {"рр2_СтараяЦерковь": "115050", "змеи": "100076", "гномы": "100076"}.get(zone) or zone_start_vnum(zone)     # церковь - plain-маршрут без клеток, отлажен пользователем от Центрального зала р2 (115050)
            _me2 = os.path.basename(os.environ.get("JMC_TARGET", "").rstrip("\\/"))
            if _sv and not zone.startswith(("переход", "закупка", "гильда")):
                for _fl in [_me2] + (["JMC БОТ ИНКА"] if COMPANION else []):
                    _cur = _wk.Jaba(os.path.join(BASE, _fl)).vnum()
                    if _cur and _cur != _sv:
                        say("не в старте зоны:", _fl, _cur, "->", _sv)
                        if not _wk.walk(_fl, _sv, say=say):
                            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: не дошла до старта зоны", zone, _fl); return "stop"
            if COMPANION:
                # «группа <имя>» переключатель: если она уже в группе - исключит (так я сама выбила Кимпи 13.11 06:44). Сначала смотрим состав.
                _p0 = log_size(); jmc("группа"); time.sleep(3); _, _gl = lines_from(_p0)
                if not any(s.split()[:1] and COMPANION[:4].lower() in s.lower() and "принята" not in s for s in _gl if "Стоит" in s or "Сидит" in s or "Отдых" in s or "Бой" in s or "Спит" in s):
                    jmc("группа " + COMPANION); time.sleep(2); say("Кимпи не было в группе - добавила")
                else:
                    say("Кимпи в группе - ок")
        except Exception as _e5:
            say("проверка старта/группы не удалась:", _e5)
        jmc(".бот старт " + zone)
    say("ПОДКЛЮЧИЛСЯ к идущей зоне" if attach else "СТАРТ зоны", zone)
    if not attach:                       # свежая жаба: бот иногда не делает первый шаг - толкаем (как вручную: перезагрузить зону, шаг 0)
        time.sleep(8)
        _, _ls = lines_from(pos)
        if not any("## STEP" in s for s in _ls):
            say("бот не сделал первый шаг - толкаю (loadZone + шаг 0)")
            for c in ("#scr botCore.enableBot = false", "#scr botCore.loadZone('%s')" % zone, "#scr botCore.waitFlag = false",
                      "#scr seekstep = 0", "#scr botCore.BotInZone = false", "#scr botCore.enableBot = true", "look краткий"):
                jmc(c); time.sleep(1)
    last_step_t = time.time(); last_idx = -1; looks = 0; start = time.time(); stops = {}; clear_t = 0; nudged_for = None; recent = []; last_vn = None; thrown = None; stopped = False; comp_seen = time.time(); comp_wait = 0; nosight = 0; area_hits = []
    while True:
        if os.path.exists(STOP):
            return "stop"
        time.sleep(8)
        pos, ls = lines_from(pos)
        text = "\n".join(ls)
        for s in ls:
            m = re.search(r"## STEP (\d+) vn=", s)
            if m:
                last_idx = int(m.group(1)); last_step_t = time.time(); looks = 0; mv = re.search(r"vn=(\d+)", s)
                if mv:
                    if last_vn and last_vn[:3] not in CITY_PREFIX and mv.group(1)[:3] in CITY_PREFIX and not zone.startswith(NOT_CITY_ZONES):
                        thrown = mv.group(1)
                    last_vn = mv.group(1)
                recent.append(last_idx); recent = recent[-40:]
        if len(recent) >= 40 and len(set(recent)) <= 4:
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "- зацикливание на шагах", sorted(set(recent))); jmc(".бот стоп"); return "stop"
        if text.count("Осушить что?") >= 5 or text.count("Вы слишком устали") >= 8:
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "- нет колб восстановления/насыщения (спам усталости)"); jmc(".бот стоп"); return "stop"
        if text.count("Вы не можете нести больше предметов") >= 3:
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "- рюкзак переполнен"); jmc(".бот стоп"); return "stop"
        if "Вам необходимо отдохнуть" in text or "Вы слишком голодны" in text:
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "- голод/усталость"); jmc(".бот стоп"); return "stop"
        if "## BOT_STOP" in text and "## ZONE_END" not in text:
            stopped = True
        if stopped and (thrown or ("Руны охранного свитка вспыхнули" in text and last_vn and last_vn[:3] not in CITY_PREFIX)):
            say("ВЫБРОС В ГОРОД (рекол/свиток/трусость), комната", thrown or "?", "- восстановление, зона", zone, "заново")
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: персонаж вышел из зоны в город (выброс/свиток/трусость или увели вручную), комната", thrown or "?", "- сам зону не перезапускаю, стоп"); jmc(".бот стоп"); return "stop"
        gb = gibberish_lines(ls) if (ls and os.environ.get("PRESENCE_ALERT")) else []
        if os.environ.get("PRESENCE_ALERT") and (len(gb) >= 3 or (re.search(r"проверк\w+ присутствия|Межреальност|ботинг", text) and "ZONE_END" not in text)):
            alert_user("Похоже, пришла ПРОВЕРКА ПРИСУТСТВИЯ (или выброс в Межреальность). Отвечай сам: молиться я здесь. Строки: " + " | ".join(gb[:3]))
        area_hits += [time.time()] * len(re.findall(r"## AREA_CHECK", text))
        area_hits = [x for x in area_hits if time.time() - x < 90]
        if len(area_hits) >= 3:
            say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "- бот снова и снова создаёт область (AREA_CHECK x%d за 90 с): потерял шаг, откатился к созданию области" % len(area_hits)); jmc(".бот стоп"); return "stop"
        if COMPANION:
            if re.search(COMPANION + r"\w* (?:здесь|стоит|летает|сидит|лежит)", text):
                comp_seen = time.time(); nosight = 0
            if re.search(COMPANION + r"\w*.{0,60}(замерл|полетел\w* на землю|оглушен|ослепл|не в силах|упал)", text, re.I) and time.time() - comp_wait > 10:
                say("спутница сбита/удержана:", COMPANION, "- жду 20 с"); jmc("#scr botCore.wait(20)"); comp_wait = time.time()
            nosight += len(re.findall(r"## STEP \d+ vn=", text))
            if nosight >= 4 and last_step_t - comp_seen > 20:      # бот шёл ещё >20 с после последнего появления спутницы (а не стоял в ожидании области)
                say("спутница", COMPANION, "отстала - пауза бота и подвожу её к лидеру")
                jmc("#scr botCore.wait(600)")
                ok = False
                try:
                    import walker as _w2
                    _me2 = os.path.basename(os.environ.get("JMC_TARGET", "").rstrip("\\/"))
                    _lead = _w2.Jaba(_me2).vnum()
                    if _lead:
                        ok = _w2.walk("JMC БОТ ИНКА", _lead, say=say)
                    if not ok:
                        # клеток новой зоны нет в графе (змеи 13.11 11:45): ведём Кимпи по пути Айлины из лога бота («## STEP n vn=X cmd=...»)
                        import mad_ctl as _mc
                        ok, _why = _mc.catch_up_by_log(); say("подвод по пути Айлины:", _why)
                except Exception as _e3:
                    say("подвести спутницу не удалось:", _e3)
                if ok:
                    comp_seen = time.time(); nosight = 0
                    jmc("#scr botCore.waitFlag = false"); jmc("#scr wTimerCount = 0"); jmc("look краткий")
                    say("спутница рядом, продолжаю", zone)
                else:
                    say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: спутницу", COMPANION, "не удалось подвести, зона", zone); jmc(".бот стоп"); return "stop"
        if re.search(r"^\d\d:\d\d:\d\d Вы мертвы|^Вы мертвы", text, re.M) or "Вы умерли" in text:
            say("СМЕРТЬ в зоне", zone, "шаг", last_idx); return "dead"
        if re.search(r"## ZONE_END", text) or re.search(r"## LEVEL_REACHED", text):
            if re.search(r"## ZONE_END", text):
                say("ZONE_END", zone)
                if pts:
                    time.sleep(2)
                    say("спидволк Б->А:", pts["B"], "->", pts["A"])
                    _walker.walk(_me, pts["A"], say=say)
                    if COMPANION:
                        _walker.walk("JMC БОТ ИНКА", pts["A"], say=say)
                return "end"
        if "## BOT_STOP" in text and "## ZONE_END" not in text:
            # плановые остановки зоны идут через ZONE_END; BOT_STOP = сбой хода
            say("BOT_STOP в зоне", zone, "шаг", last_idx); time.sleep(3)
            if not zone.startswith(NOT_CITY_ZONES):
                vv = get_vnum()
                if vv and vv[:3] in CITY_PREFIX and last_vn and last_vn[:3] not in CITY_PREFIX:
                    say("ВЫБРОС В ГОРОД (рекол/свиток/трусость), комната", vv, "- восстановление, зона", zone, "заново")
                    jmc(".бот стоп"); say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: выброс в город, зона", zone); return "stop"
            stops[last_idx] = stops.get(last_idx, 0) + 1
            if stops[last_idx] >= 3:
                say("!!! ТРЕБУЕТСЯ ЧЕЛОВЕК/КЛОД: зона", zone, "шаг", last_idx, "- 3 раза BOT_STOP на одном шаге, чинка не помогает. Останавливаюсь.")
                jmc(".бот стоп"); return "stop"
            # одна попытка: ворота / повтор шага
            jmc("отпер ворота;откр ворота"); time.sleep(2)
            jmc("#scr seekstep = %d" % (max(last_idx, 0) + 1))
            jmc("#scr botCore.enableBot = true"); jmc("look краткий")
            last_step_t = time.time(); continue
        for pat in ("Вы не можете идти в этом направлении", "Бот отключен", "СтатСтоп ОШИБКА"):
            if pat in text:
                say("СОБЫТИЕ:", pat, "| шаг", last_idx, "- чиню (look + повтор шага)")
                jmc("#scr seekstep = %d" % max(last_idx - 1, 0)); jmc("#scr botCore.enableBot = true"); jmc("look краткий")
                last_step_t = time.time(); looks = 0; break
        _aw = re.search(r"## AREA_WAIT secs=(\d+)", text)
        if _aw:      # бот законно ждёт КД области у входа: это не застой (13.11 10:56 круг остановился на 400 с при ожидании 466 с)
            last_step_t = time.time() + int(_aw.group(1)); looks = 0
            say("жду КД области", _aw.group(1), "с, зона", zone)
        idle = time.time() - last_step_t
        if "Очередь команд очищена" in text:
            clear_t = time.time()
        if clear_t > last_step_t and time.time() - last_step_t > 4 and nudged_for != last_step_t:
            nudged_for = last_step_t              # очередь очищена (пом без цели/ошибка) - ход потерян: толкаем сразу, не ждём 60 с
            jmc("look краткий")
        if idle > 60 and looks == 0:
            jmc("look краткий"); looks = 1
        elif idle > 90 and looks == 1:
            if "Попробуйте сначала открыть" in "\n".join(lines_from(max(0, pos - 4000))[1]):
                jmc("отпер ворота;откр ворота"); time.sleep(2)
            jmc("#scr seekstep = %d" % (max(last_idx, 0) + 1)); jmc("look краткий"); looks = 2
            say("застой на шаге", last_idx, "- повтор шага")
        elif idle > 180 and looks == 2:
            jmc("look краткий"); looks = 3
        elif idle > 400:
            say("ЗАСТОЙ >400 с, зона", zone, "шаг", last_idx); return "stop"
        if time.time() - start > 3 * 3600:
            say("зона идёт >3 ч, пропуск", zone); return "stop"


GUILD_UP = "путь варвар;уч доп 5;уч атак 5;уч дубин 10;трен тело;путь склад"   # универсально, 13-18 лвл, после каждой зоны (слова пользователя 12.11)


def wait_quiet(min_s=20, quiet_s=10, max_s=240):
    """Ждать, пока лог игры не затихнет (дошли/отучились)."""
    t0 = time.time(); last = log_size(); last_t = time.time()
    while time.time() - t0 < max_s:
        time.sleep(2)
        s = log_size()
        if s != last:
            last = s; last_t = time.time()
        elif time.time() - t0 > min_s and time.time() - last_t > quiet_s:
            return


def go_path(cmd, timeout=120):
    """«путь X» асинхронный: следующая команда в той же строке выполняется до прибытия (и путь склад перебивает его). Шлём путь отдельно и ждём «Вы достигли пункта назначения»."""
    pos = log_size(); jmc(cmd); t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(2)
        _, ls = lines_from(pos)
        txt = "\n".join(ls)
        if "Вы достигли пункта назначения" in txt:
            time.sleep(1); return True
        if "Не найден" in txt or "не найден" in txt or "Нет пути" in txt:
            return False
    return False


def do_seq(cmds):
    for c in cmds:
        if c.startswith("путь "):
            go_path(c)
        else:
            jmc(c); time.sleep(2.5)

BAD_COND = r"\[(плохое|очень плохое|ужасное|отвратительное|сломан\w*|разбит\w*)\]"
REPAIR = "путь ремонт;чин все;путь склад"      # слова пользователя 12.11: после зоны, если экип в плохом состоянии и хуже


def repair_if_needed(zone):
    if zone.startswith(("гильда", "переход", "ремонт")):
        return
    pos = log_size(); jmc("экип"); time.sleep(3)
    _, ls = lines_from(pos)
    bad = [s.strip() for s in ls if re.search(BAD_COND, s)]
    if bad:
        say("ЭКИП в плохом состоянии (%d предм.): %s -> %s" % (len(bad), "; ".join(b[:40] for b in bad[:3]), REPAIR))
        run_zone("ремонт")
        pos = log_size(); jmc("экип"); time.sleep(3)
        _, ls = lines_from(pos)
        left = [s.strip() for s in ls if re.search(BAD_COND, s)]
        say("после ремонта плохих предметов:", len(left))

def guild_up_if_needed(zone):
    if zone.startswith(("гильда", "переход", "закупка", "леч", "ремонт")):
        return
    lvl = get_level()
    if lvl is not None and 13 <= lvl <= 18:
        say("ГИЛЬДИЯ-ПРОКАЧКА (лвл %d):" % lvl, GUILD_UP)
        run_zone("гильда_уч")


LIGHT_ZONES = ("канал", "болото", "склад1", "привы1")      # слова пользователя 12.11: свет проверять только перед этими зонами


def ensure_light(zone):
    """Перед канал/болото/склад1/привы1: на нас должен быть «магический свет» (свиток солнца: зач солнц)."""
    if zone not in LIGHT_ZONES:
        return
    pos = log_size(); jmc("аф"); time.sleep(3)
    _, ls = lines_from(pos)
    if any("магический свет" in s for s in ls):
        return
    pos = log_size(); jmc("инв"); time.sleep(3)
    _, ls = lines_from(pos)
    if not any("свиток солнца" in s for s in ls):
        say("нет свитков солнца - беру 2 с КСК"); jmc("#2 кз :колбы солн"); time.sleep(3)
    say("нет маг.света перед", zone, "- зач солнц"); jmc("зач солнц"); time.sleep(3)

CIRCLE = ["каты2", "переход_р1", "порт", "переход_р2", "гоблины", "чайный_домик", "привы2", "склад2"]   # круг 18-20 лвл (слова пользователя)


def circle_until_20(attach=False, start_zone=None):
    """После гильда17 крутим круг до 20 лвл; каты2 только с 18. На 20: стоп (сет3, заточка перчаток, Эрдер - вручную/по слову)."""
    k = CIRCLE.index(start_zone) if start_zone in CIRCLE else 0
    while True:
        lvl = get_level()
        if lvl is not None and lvl >= 21:
            say("!!! ГОТОВО: достигнут 21 уровень"); return
        zone = CIRCLE[k % len(CIRCLE)]; k += 1
        if zone == "каты2" and (lvl is None or lvl < 18):
            continue
        if zone in ("переход_р1", "переход_р2"):
            v = None
        say("КРУГ: уровень", lvl, "| зона", zone)
        if not attach:
            ensure_light(zone)
        r = run_zone(zone, attach); attach = False
        if r == "restart":
            k -= 1; continue
        if r != "end":
            say("остановка круга:", r, "зона", zone); return
        repair_if_needed(zone)
        guild_up_if_needed(zone)

def main():
    start_from = None
    if "--from" in sys.argv:
        start_from = sys.argv[sys.argv.index("--from") + 1]
    if os.path.exists(STOP):
        os.remove(STOP)
    say("надсмотрщик запущен; лог игры:", LOG)
    if "--circle" in sys.argv:
        circle_until_20("--attach" in sys.argv, sys.argv[sys.argv.index("--zone") + 1] if "--zone" in sys.argv else None); return
    i = 0
    if start_from:
        i = [p[0] for p in PLAN].index(start_from)
    fill = 0
    first = True
    if "--recover" in sys.argv:
        recover_after_throw(PLAN[i][0])
    while i < len(PLAN):
        zone, minlvl, pre = PLAN[i]
        lvl = get_level()
        say("уровень по сч:", lvl, "| следующая зона:", zone, "(нужно >=", minlvl, ")")
        if lvl is not None and lvl >= 18 and lvl < minlvl and zone not in ("школа",) and not zone.startswith(("гильда", "переход", "закупка")):
            # добор опыта: повтор последней боевой зоны ПЛАНА (не каты2 на низком уровне!); круг FILLER только с 18 лвл
            if lvl >= 18:
                f = FILLER[fill % len(FILLER)]; fill += 1
            else:
                j = i - 1
                while j > 0 and PLAN[j][0].startswith(("гильда", "переход", "закупка", "леч")): j -= 1
                f = PLAN[max(j, 0)][0]
            say("уровня не хватает - добираем зоной", f)
            r = run_zone(f)
            if r != "end":
                say("остановка:", r); return
            continue
        attach = ("--attach" in sys.argv) and first
        first = False
        if pre and not attach:
            for c in pre.split(";"):
                jmc(c); time.sleep(4)
        if not attach:
            ensure_light(zone)
        r = run_zone(zone, attach)
        if r == "restart":
            first = False; continue
        if r != "end":
            say("остановка:", r, "зона", zone); return
        repair_if_needed(zone)
        guild_up_if_needed(zone)
        i += 1
    say("линейная часть плана пройдена; уровень:", get_level(), "- дальше круг до 20 лвл")
    circle_until_20()


if __name__ == "__main__":
    main()
