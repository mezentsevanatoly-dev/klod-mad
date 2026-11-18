"""Прокачка Кимпи в группе Айлины: kimpi_level.py [до_уровня=30] зона1 зона2 ... [--loop] [--cd=30]
Айлина (лидер) — bot_batch по зоне; Кимпи следует. Зона с целями — не чаще раза в cd минут (таймер области/репопа);
переход_* — всегда. Нет ни одной готовой зоны — ждать минуту. После зоны: опыт Кимпи (сч), где стоит.
Кимпи отстала -> довести к Айлине (go_any) + «след айл». Стоп: уровень достигнут, JMC закрыта (нет ответа), смерть, партия не дошла.
Лог: mudbot\\data\\kimpi_level.log"""
import os, sys, re, time, subprocess
T = os.path.dirname(os.path.abspath(__file__))
R = r"C:\Users\User\Desktop\Клод мад"
AIL = os.path.join(R, "JMC БОТ АЙЛИНА"); KIM = os.path.join(R, "JMC БОТ ИНКА")
LOG = os.path.join(os.path.dirname(T), "data", "kimpi_level.log")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
goal = int(args[0]) if args and args[0].isdigit() else 30
zones = [a for a in args if not a.isdigit()]
loop = "--loop" in sys.argv
CD = 60 * float(next((a[5:] for a in sys.argv if a.startswith("--cd=")), "30"))


def run(script, *a, target=AIL, timeout=3600):
    env = dict(os.environ, JMC_TARGET=target)
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, script)] + list(a), capture_output=True, text=True, encoding="utf-8", env=env, cwd=T, timeout=timeout)
    return r.stdout + r.stderr


def where(target):
    m = re.search(r"\['(\d+)', '([^']*)', '([^']*)'\]", run("where.py", target=target))
    return m.groups() if m else (None, None, None)


def kimpi_state():
    out = run("cmd.py", "сч", "3", target=KIM)
    lv = re.search(r"Варвар (\d+) уровня", out); need = re.search(r"надо набрать (\d+) опыта", out)
    return (int(lv.group(1)) if lv else None), (int(need.group(1)) if need else None)


def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True); open(LOG, "a", encoding="utf-8").write(s + "\n")


lv, need = kimpi_state()
if lv is None: say("СТОП: JMC Кимпи не отвечает"); sys.exit(1)
say("СТАРТ: Кимпи", lv, "ур., до следующего", need, "| цель", goal, "| зоны:", " ".join(zones), "| таймер", CD / 60, "мин")
last = {}; k = 0; idle_cycle = True
while zones:
    if lv and lv >= goal: say("ЦЕЛЬ: Кимпи", lv, "уровня"); break
    if k >= len(zones):
        if not loop: break
        if idle_cycle: time.sleep(60)
        k = 0; idle_cycle = True
    z = zones[k]; k += 1
    is_move = z.startswith("переход")
    if not is_move and time.time() - last.get(z, 0) < CD:
        continue
    a = where(AIL); b = where(KIM)
    if a[0] is None or b[0] is None: say("СТОП: JMC не отвечает (Айлина %s, Кимпи %s)" % (a[0], b[0])); break
    if b[0] != a[0]:
        say("Кимпи не рядом:", b, "-> веду к Айлине", a)
        run("go_any.py", a[0], target=KIM); run("cmd.py", "след айл", "2", target=KIM)
    t0 = time.time()
    out = run("bot_batch.py", z)
    res = [l for l in out.splitlines() if "ИТОГ" in l or "не дошла" in l or "СТОП" in l]
    kills = [l for l in out.splitlines() if l.startswith("убила")]
    lv2, need2 = kimpi_state()
    if lv2 is None: say("СТОП: JMC Кимпи не отвечает после", z); break
    gain = (need - need2) if (need and need2 and lv2 == lv) else ("новый уровень %s!" % lv2 if lv2 > lv else "?")
    say("%-16s %4.1f мин | Кимпи %s ур., до след. %s, получила %s | %s | %s" % (z, (time.time() - t0) / 60, lv2, need2, gain, (res[-1] if res else "?")[:70], (kills[-1] if kills else "")[:150]))
    if not is_move:
        last[z] = time.time(); idle_cycle = False
    if any("не дошла" in l or "СТОП" in l for l in res): say("СТОП: партия не прошла зону", z); break
    lv, need = lv2, need2
say("КОНЕЦ: Кимпи", lv, "ур.", where(KIM), "| Айлина", where(AIL))
