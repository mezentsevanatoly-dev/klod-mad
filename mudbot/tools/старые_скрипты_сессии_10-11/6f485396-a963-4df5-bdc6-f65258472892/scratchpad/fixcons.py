import os, re, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
os.environ["MUD_VIA"] = "bot"
import barb_levelup as B
words = ("настойка.насыщ", "настойка.насыщ", "настойка.восст", "настойка.восст", "настойка.восст", "эликсир.прозр", "эликсир.летуч",
         "охранн.свиток", "свиток.панац")
for w in words:
    out = B.cmd(f"кз :следак1 {w}", wait=2)
    if "забрали" in out:
        o2 = B.cmd(f"кс :колбы {w}", wait=2)
        print(w, "->колбы" if "сдали" in o2 else "НЕ СДАНО " + o2[-100:])
    else:
        print(w, "нет")
print(B.cmd("ксклад :следак1", wait=2)[-500:])
