"""Воспроизвести команды пользователя из JMC-лога по порядку, со сверкой комнат (без импровизации).

  python tools/log_play.py <лог> <с_строки> <по_строку> --dry     только разобрать и показать
  python tools/log_play.py <лог> <с_строки> <по_строку>           играть

Команда = строка лога, равная набранной пользователем команде (направления, убить, взя*, отпер*, откр*, г, груп, дать, осуш, сорвать,
яр и, очистить, вст, смотреть, разбить…). После хода ждём MSDP-комнату и сверяем название с тем, что в логе (первая строка-заголовок
после хода); не совпало — стоп и отчёт. В бою (в промпте есть [имя:состояние]) следующую команду не шлём, пока бой не кончится.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX, OUT = os.path.join(HERE, "inbox.txt"), os.path.join(HERE, "out.log")
JMC = os.path.join(os.path.dirname(HERE), "JMC")
MOVES = {"север", "юг", "запад", "восток", "вверх", "вниз"}
MAP = re.compile(r"^[+|:~ .@mMGROR%=$\"#?_\]!>v^/\-]+$")
CMD = re.compile(r"^(север|юг|запад|восток|вверх|вниз|убить .+|взя.*|отпер.*|откр.*|г .+|груп.*|дать .+|осуш.*|сорвать.*|яр и|очистить|вст|смотреть.*|см .+|"
                 r"разбить.*|отдых.*|зада|тр|мс|мв|ка .+|к .+|надеть.*|од .*|снять.*|держ.*)$")
PROMPT = re.compile(r"^\d+H \d+M \d+V")
SKIP_CMD = re.compile(r"^(смотреть|см |зада|к |ка |тр$|мс$|мв$)")         # справочные и боевые умения пропускаем: бой ведёт бот/удар по умолчанию


def parse(name, a, b):
    L = [l.rstrip("\r") for l in open(os.path.join(JMC, name), "rb").read().decode("cp1251", "replace").split("\n")]
    cmds = []
    loose = "--loose" in sys.argv
    moves_only = "--moves" in sys.argv                     # только ходы и «убить»: всё, что делают триггеры (двери, лут, очистить, вст), не повторяем
    for i in range(a, min(b, len(L))):
        s = L[i].strip()
        if moves_only and not (s in MOVES or s.startswith("убить ") or s in ("г помогу", "г видел", "груп все", "гр все", "сорвать ковер", "дать посох отшель",
                                                                                "отпер сун", "откр сун", "взя все сун")):
            continue
        if loose:                                          # любая набранная пользователем строка: короткая, со строчной буквы, без знаков препинания, не карта/промпт
            if not (s and len(s) <= 40 and s[0].islower() and not re.search(r"[.,!?:;\[\]()]", s) and not MAP.match(s) and not PROMPT.match(s) and not s.startswith("<<H")):
                continue
        elif not CMD.match(s):
            continue
        # заголовок комнаты после хода
        title = None
        if s in MOVES:
            for j in range(i + 1, min(i + 40, len(L))):
                t = L[j]
                if t.startswith("[ Exits:"):
                    break
                if t.strip() and not t.startswith("   ") and not MAP.match(t.strip()) and not PROMPT.match(t.strip()) and not t.startswith("<<H") and len(t.strip()) < 48 and not t.strip().endswith((".", "!", "?")):
                    nxt = [x for x in L[j + 1:j + 12] if x.startswith("[ Exits:")]
                    if nxt:
                        title = t.strip()
                        break
        cmds.append((i, s, title))
    return cmds


def last_prompt():
    try:
        with open(OUT, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 6000))
            t = f.read().decode("utf-8", "replace")
    except OSError:
        return ""
    ps = re.findall(r"<<H.*?>>>", t)
    return ps[-1] if ps else ""


def in_battle():
    p = last_prompt()
    return bool(re.search(r"\[[^\]]+:[^\]]+\]\s*\[[^\]]+:[^\]]+\]", p)) or "Вых" in p and re.search(r"\]\s+\[", p) is not None


def cur_room():
    try:
        with open(OUT, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 30000))
            t = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    m = re.findall(r"\[msdp\] комната (\d+) \| (.*?) \| (.*?) \|", t)
    return m[-1] if m else None


def send(c):
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(c + "\n")


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    name, a, b = args[0], int(args[1]), int(args[2])
    cmds = parse(name, a, b)
    print(f"команд: {len(cmds)} (строки {a}–{b})", flush=True)
    if "--dry" in sys.argv:
        for i, s, t in cmds:
            print(f"{i}: {s}" + (f"  -> {t}" if t else ""))
        return
    k = -1
    while k + 1 < len(cmds):
        k += 1
        i, s, title = cmds[k]
        t0 = time.time()
        while in_battle() and time.time() - t0 < 90:
            time.sleep(0.8)
        before = cur_room()
        send(s)
        time.sleep(0.9 if s in MOVES else 1.4)
        if s in MOVES and title and "--loose" not in sys.argv and "--moves" not in sys.argv:
            t1 = time.time()
            while time.time() - t1 < 6:
                now = cur_room()
                if now and (before is None or now != before):
                    break
                time.sleep(0.3)
            now = cur_room()
            if not now or (title not in now[2] and now[2] not in title):
                nk = next((q for q in range(k + 1, min(k + 16, len(cmds))) if cmds[q][2] and (cmds[q][2] in now[2] or now[2] in cmds[q][2])), None) if now else None
                if nk is not None:                         # мы впереди/сбоку лога: переходим на ближайшую команду, ждущую эту комнату
                    print(f"  пересинхронизация: «{now[2]}» — переход к команде #{nk} (строка {cmds[nk][0]})", flush=True)
                    k = nk
                    continue
                print(f"СТОП на команде #{k} «{s}» (строка лога {i}): ждали «{title}», мы в «{now[2] if now else '?'}» ({now[0] if now else '?'})", flush=True)
                return
    print("лог воспроизведён до конца", flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
