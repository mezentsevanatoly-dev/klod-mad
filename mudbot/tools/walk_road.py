"""Идти по дороге, выбирая выход без возврата назад, пока не встретится комната с заданным названием.

  python tools/walk_road.py "Дорога в холмы" [макс_шагов] [предпочтение, напр. ESNW]
Печатает каждую комнату (vnum, название, выходы). Для разведки линейных дорог.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
BACK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}


def go(cmdline):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py"), cmdline + "|1.3"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    m = re.findall(r"\[cur\] \{'vnum': '(\d+)', 'area': '([^']*)', 'name': '([^']*)', 'exits': \{([^}]*)\}", r.stdout.replace("\n", " "))
    if not m:
        return None
    v, a, n, ex = m[-1]
    return v, a, n, dict(re.findall(r"'([NSEWUD])': '(\d+)'", ex))


def main(target, maxsteps=40, prefer="ESNW"):
    cur = go("где")
    seen = {cur[0]}
    came = None
    print(cur[0], cur[2], "".join(cur[3]))
    for _ in range(maxsteps):
        if cur[2] == target:
            print("НАШЛА:", cur[0], cur[2], "".join(cur[3]))
            return
        opts = [d for d in prefer if d in cur[3] and d != BACK.get(came or "", "") and cur[3][d] not in seen]
        if not opts:
            opts = [d for d in prefer if d in cur[3] and cur[3][d] not in seen]
        if not opts:
            print("тупик/круг:", cur)
            return
        d = opts[0]
        nxt = go(WORD[d])
        if not nxt or nxt[0] == cur[0]:
            print("не сдвинулась:", d, nxt)
            return
        came = d
        cur = nxt
        seen.add(cur[0])
        print(f"{d} -> {cur[0]} {cur[1]} | {cur[2]} | {''.join(cur[3])}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40, sys.argv[3] if len(sys.argv) > 3 else "ESNW")
