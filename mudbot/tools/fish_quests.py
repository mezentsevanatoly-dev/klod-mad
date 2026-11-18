"""Квесты Деревни рыбаков по тексту игры (читает out.log, команды кладёт в inbox.txt). Запускается рядом с обходом зоны.

  Контар:  в комнате с «огромным зеркалом в граненом багете» -> `разбить зеркало`; убить повелителя зеркала (бьёт обход),
           подобрать осколок; у Контара («по имени Контар») -> `дать оскол конта`.
  Вдова:   убить разъярённого энта (бьёт обход), подобрать амулет из корней дуба; у вдовы («потерявшая мужа») -> `дать аму вдов`.
Отшельник и капитан в логе пользователя (рыбка) уже сделаны. Остановка: оба квеста выполнены или файл tools/fish_quests.stop.
  python tools/fish_quests.py
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, INBOX = os.path.join(HERE, "out.log"), os.path.join(HERE, "inbox.txt")
STOP = os.path.join(HERE, "tools", "fish_quests.stop")
LOG = os.path.join(HERE, "tools", "fish_quests.log")

HERMIT = "--hermit" in sys.argv                    # режим отшельника: Контар и вдова уже сданы, наблюдатель работает до stop-файла
st = {"amulet": False, "shard": False, "widow": False, "kontar": False, "mirror_tries": 0, "last": {}}


def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def send(cmd):
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(cmd + "\n")
    say("отправила:", cmd)


def once(key, gap=6):
    """Не повторять одну и ту же команду чаще чем раз в gap секунд."""
    t = time.time()
    if t - st["last"].get(key, 0) < gap:
        return False
    st["last"][key] = t
    return True


def handle(s):
    if "Вы взяли амулет из корней дуба" in s:
        st["amulet"] = True
        say("амулет у меня")
    if "Вы взяли осколок зеркала" in s:
        st["shard"] = True
        say("осколок у меня")
    if "Вдова дала вам" in s:
        st["widow"] = True
        say("квест вдовы выполнен:", s)
    if "Управляющий Контар дал вам" in s:
        st["kontar"] = True
        say("квест Контара выполнен:", s)
    if HERMIT:
        if "Попробуйте сначала открыть" in s and once("doors", 8):
            for d in ("север", "юг", "запад", "восток"):          # как макрос пользователя: отпереть и открыть дверь по всем сторонам
                send("отпер две " + d)
                send("откр две " + d)
        if "Вы взяли красный ключик" in s:
            st["redkey"] = True
            say("красный ключик у меня")
        if st.get("redkey") and "сундук" in s and ("стоит" in s or "лежит" in s) and once("chest", 20):
            for c in ("отпер сун", "откр сун", "взя все сун", "взя все"):
                send(c)
        if "Вы взяли посох, покрытый голубым металлом" in s and once("staff", 10):
            send("дать посох отшель")
            say("посох отдан отшельнику")
        if "отшельник стоит здесь" in s and not st.get("hermit_in") and once("hermit", 15):
            send("г помогу")                                   # отшельник просит помочь попасть в сокровищницу (лог пользователя)
        if "Отшельник теперь следует за вами" in s:
            st["hermit_in"] = True
            send("груп все")
            say("отшельник в группе")
    if "потерявшая мужа" in s and st["amulet"] and not st["widow"] and once("widow"):
        send("дать аму вдов")
    if "по имени Контар" in s and st["shard"] and not st["kontar"] and once("kontar"):
        send("дать оскол конта")
    if "Огромное зеркало в граненом багете стоит здесь" in s and not st["shard"] and st["mirror_tries"] < 3 and once("mirror", 30):
        st["mirror_tries"] += 1
        send("разбить зеркало")


def main():
    if os.path.exists(STOP):
        os.remove(STOP)
    pos = os.path.getsize(OUT)
    buf = b""
    say("наблюдатель квестов запущен")
    while not os.path.exists(STOP):
        time.sleep(0.3)
        with open(OUT, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size < pos:
                pos = 0
            f.seek(pos)
            buf += f.read()
            pos = f.tell()
        *lines, buf = buf.split(b"\n")
        for raw in lines:
            handle(raw.decode("utf-8", "replace").strip())
        if st["widow"] and st["kontar"] and not HERMIT:
            say("оба квеста выполнены, останавливаюсь")
            return


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
