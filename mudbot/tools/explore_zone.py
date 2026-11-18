"""Эксплор соседней зоны: дойти до клетки перехода, шагнуть в зону, запустить эксплор, дождаться конца.
python -X utf8 tools/explore_zone.py <клетка_перехода> <направление>
Пример: explore_zone.py 115080 восток   (из Геоланта в «Склад в Геоланте»)"""
import os, sys, time, re
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc, speedwalk


def where():
    s = jmc.log_size()
    jmc.type_line("#scr ClaudeLog.note('WHERE $MsdpRoomVnum|$MsdpRoomArea')", force=True)   # одинарные: в названиях зон бывают двойные кавычки
    time.sleep(1)
    for l in jmc.read_log(s):
        if "## WHERE " in l:
            v, a = l.split("## WHERE ")[1].strip().split("|", 1)
            return v, a
    return None, None


def walk(target):
    """Путь одной строкой; если бой/очистка очереди остановили на полпути — дождаться и дослать от текущей клетки."""
    G, names = speedwalk.graph()
    for attempt in range(6):
        cur, _ = where()
        if cur == target:
            return True
        p = speedwalk.path(cur, target, G)
        if p is None:
            print("нет пути из", cur, "в", target); return False
        if attempt:
            print("досылаю путь из", cur, "(попытка %d)" % (attempt + 1))
            time.sleep(6)                          # дать закончиться бою
        jmc.type_line(";".join(p), force=True)
        time.sleep(max(3, len(p) * 0.15))
    return where()[0] == target


if sys.argv[1] == "here":                     # эксплор зоны, в которой уже стоим
    v, a = where()
    print("здесь:", a, v)
else:
    frm, d = sys.argv[1], sys.argv[2]
    if not walk(frm):
        sys.exit("не дошла до " + frm)
    _, a0 = where()
    jmc.type_line(d, force=True)
    time.sleep(2)
    v, a = where()
    if a == a0:
        sys.exit("шаг %s из %s не привёл в другую зону (стою %s, %s)" % (d, frm, v, a))
    print("вошла:", a, v)


def alarm():
    """Окно поверх всех; по OK — переключиться на JMC."""
    import ctypes
    u = ctypes.WinDLL("user32")
    u.MessageBoxW(0, "Бот стоит больше 10 секунд. OK — открыть JMC.", "МАД: бот стоит", 0x40 | 0x40000 | 0x1000)
    h = jmc.find_window()
    u.ShowWindow(h, 9)
    u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0)   # Alt — чтобы Windows разрешил вывести окно вперёд
    u.SetForegroundWindow(h)


s = jmc.log_size()
jmc.type_line("эксплор", force=True)
t0 = last_move = time.time()
end = None
while time.time() - t0 < 1800:
    time.sleep(2)
    for l in jmc.read_log(s):
        if "[ Exits:" in l:
            last_move = time.time()
        if "EXPLORE" in l:
            print(l.strip())
            if re.search(r"EXPLORE (ГОТОВО|СТОП|НЕТ ПОЛЁТА)", l):
                end = l
    s = jmc.log_size()
    if end:
        break
    if time.time() - last_move > 10:
        print("стоит >10 с — окно пользователю")
        alarm()
        last_move = time.time()
print("ИТОГ:", end or "не дождалась конца за 15 минут")
