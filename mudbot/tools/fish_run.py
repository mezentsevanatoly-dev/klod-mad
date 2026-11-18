"""Деревня рыбаков: создать область у входа (Лесная тропка), зайти, обойти зону (по одному мобу на имя) с квестами Контара и вдовы,
вернуться пешком и записать спидволки от площади Элендора до входа и обратно.
Запускать, когда персонаж стоит на клетке входа («Лесная тропка», выход на юг в Деревню рыбаков).
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import zone_survey as zs

ZONE = "Деревня рыбаков"
ENTRY = "111080"          # Лесная тропка (Болото): выход на юг -> 117094


def main(minutes=22):
    zs.say("старт; где:", zs.where())
    if zs.where()[1] != ZONE:                                  # уже внутри (перезапуск) — вход пропускаем
        if zs.where()[0] != ENTRY and not zs.walk_to(ENTRY):
            zs.say("не дошла до клетки входа — стоп")
            return
        t = zs.cmd(["область создать ю"], 5)
        zs.say("область:", " ".join(t.split())[-120:])
        zs.cmd(["юг"], 3)
        if zs.where()[1] != ZONE:
            zs.say("не вошла в зону:", zs.where())
            return
    zs.say("в зоне", ZONE, zs.where())
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    q = subprocess.Popen([sys.executable, "-X", "utf8", os.path.join("tools", "fish_quests.py")], cwd=HERE, env=env,
                         stdout=open(os.path.join(HERE, "tools", "run_fish_quests.log"), "w", encoding="utf-8"), stderr=subprocess.STDOUT)
    p = subprocess.Popen([sys.executable, "-X", "utf8", os.path.join("tools", "mapfight.py"), "99", "--survey", "--once", "--zone", ZONE,
                          "--extra", "4", "--below", "99", "--skip", "0",
                          "--never", "капитан эльфийского судна,отшельник,потерявшая мужа,контар"], cwd=HERE, env=env,
                         stdout=open(os.path.join(HERE, "tools", "run_survey_Деревня_рыбаков.log"), "w", encoding="utf-8"), stderr=subprocess.STDOUT)
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < minutes * 60:
        time.sleep(10)
    if p.poll() is None:
        p.kill()
    open(os.path.join(HERE, "tools", "fish_quests.stop"), "w").close()
    time.sleep(1.5)
    zs.say("обход закончен, иду к входу пешком")
    zs.walk_to(ENTRY)
    import zone_walks_from_graph as zw
    zw.main([ZONE])
    zs.say("готово")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
