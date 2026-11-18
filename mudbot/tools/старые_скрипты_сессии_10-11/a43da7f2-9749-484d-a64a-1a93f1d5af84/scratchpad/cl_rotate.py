p = r"C:\Users\User\Desktop\Клод мад\Тадия\scripts\ClaudeLog.js"
s = open(p, "rb").read().decode("cp1251")
if "this.curDay" not in s:
    s = s.replace('''			var f = fso.OpenTextFile("claude_game.log", 8, true);''', '''			var day0 = d.getFullYear() + "-" + this.pad(d.getMonth() + 1) + "-" + this.pad(d.getDate());
			if (this.curDay != day0) {   // daily rotation: claude_game.log holds ONLY today; full history is in Logs\\\\game_DATE.log
				if (this.curDay == null) {
					if (fso.FileExists("claude_game.log")) {
						var lm = fso.GetFile("claude_game.log").DateLastModified, ld = new Date(lm);
						var lday = ld.getFullYear() + "-" + this.pad(ld.getMonth() + 1) + "-" + this.pad(ld.getDate());
						if (lday != day0) { var t0 = fso.CreateTextFile("claude_game.log", true); t0.Close(); }
					}
				} else { var t1 = fso.CreateTextFile("claude_game.log", true); t1.Close(); }
				this.curDay = day0;
			}
			var f = fso.OpenTextFile("claude_game.log", 8, true);''', 1)
    s = s.replace('this.moduleName = "ClaudeLog";', 'this.moduleName = "ClaudeLog"; this.curDay = null;', 1)
    s = s.replace("claude_game.log (current) and Logs\\game_YYYY-MM-DD.log (per day).", "claude_game.log (TODAY ONLY, rotated daily) and Logs\\game_YYYY-MM-DD.log (per day, full history).", 1)
    open(p + ".bak_rotate", "wb").write(open(p, "rb").read())
    open(p, "wb").write(s.encode("cp1251"))
print("curDay" in s, len(s))
