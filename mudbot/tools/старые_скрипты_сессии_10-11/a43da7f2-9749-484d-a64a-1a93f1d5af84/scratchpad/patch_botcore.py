import shutil, sys
p = r"C:\Users\User\Desktop\Тадия\scripts\BotCore.js"
shutil.copyfile(p, p + ".bak_watch")
s = open(p, "rb").read().decode("cp1251")
CL = 'if (typeof ClaudeLog != "undefined") ClaudeLog.note('

def rep(old, new):
    global s
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)

# 1. старт зоны
rep('// Claude: перед стартом зоны проверить аффекты', CL + '"BOT_START zone=" + zonename + " steps=" + zons.length); // Claude: перед стартом зоны проверить аффекты')
# 2. стоп
rep('jmc.showme ( color(0,36)+"Бот отключен"+color(0,0));', CL + '"BOT_STOP step=" + seekstep + "/" + zons.length); jmc.showme ( color(0,36)+"Бот отключен"+color(0,0));')
# 3. конец зоны
rep('jmc.showme ( color(1,36)+"[Бот: зона \'"+zonename+"\' закончена]"+color(0,0));', CL + '"ZONE_END zone=" + zonename + " steps=" + zons.length); jmc.showme ( color(1,36)+"[Бот: зона \'"+zonename+"\' закончена]"+color(0,0));')
# 4. ход отклонён боем
rep("jmc.showme('-:- Ход не прошёл (бой), повторяю шаг ' + seekstep);",
    "jmc.showme('-:- Ход не прошёл (бой), повторяю шаг ' + seekstep); " + CL + '"MOVE_BLOCKED_BATTLE step=" + seekstep);')
open(p, "wb").write(s.encode("cp1251"))
print("ok")
