import os, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
os.environ["MUD_VIA"] = "bot"
import barb_levelup as B
B.reequip()
print(B.cmd("инв", wait=2)[-600:])
print(B.cmd("аф", wait=2)[-500:])
