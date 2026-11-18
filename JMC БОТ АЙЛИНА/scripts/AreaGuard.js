// AreaGuard: the route line ".триг обл с <напр>" (create an area) is replaced by a checked sequence:
//   1) "обл" -> read the table of our areas;
//   2) a row of this zone with status "готов к удалению" / "удалите вручную" -> "обл удал <напр>", then create again;
//   3) if the game answers "Вы сможете создать новый экземпляр ... через N мин" -> wait N min + 1 min, repeat the check;
//   4) after "Создан экземпляр" -> "обл" again and save "zone|created|repop|expiry(= created + repop + 1 min)" to areas/area_timers.txt.
// ".бот обл" shows the saved timers. Safe to include again (wraps the original handlers once). Needs BotCore.js.
var AREA_NOWAIT = {"рр2_СтараяЦерковь": 1, "притон": 1, "склад1": 1, "привы1": 1, "леч": 1, "каты1": 1, "привы2": 1, "склад2": 1, "гоблины": 1, "чайный_домик": 1, "рыбка": 1, "кочи": 1, "конюшни": 1, "ель": 1, "каты2": 1, "24плюс": 1, "церковь": 1, "ящеры": 1};   // zones where a cooldown is NOT waited for: walk into the existing area / the zone at once
var AREA_NAMES = {"гномы": "Подземелье гномов", "змеи": "Змеиное гнездо", "рр2_СтараяЦерковь": "Старая церковь", "ящеры": "Селение человекоящеров", "бесы": "Тоннель бесов", "парк": "Парк", "аллея": "Аллея", "канал": "Канализация", "притон": "Притон", "склад1": "Склад в Геоланте", "привы1": "Дом с привидениями", "леч": "Лечебница для животных", "каты1": "Катакомбы Геоланта", "привы2": "Дом с привидениями", "склад2": "Склад в Геоланте", "гоблины": "Лагерь гоблинов", "чайный_домик": "Чайный домик", "рыбка": "Деревня рыбаков", "кочи": "Лагерь кочевников", "конюшни": "Конюшни", "каты2": "Катакомбы Геоланта", "24плюс": "Трактир \"У Лиса\"", "геоканал3": "Катакомбы Геоланта", "храм": "Храм пламенного меча", "ель": "Лагерь археологов"};   // bot zone name -> zone name in the "обл" table (add new zones here)

(function () {
	var core = botCore;
	if (!core.origNextStepArea) {
		core.origNextStepArea = core.nextStep;
		core.origOnIncomingArea = core.onIncoming;
		core.origOnTimerArea = core.onTimer;
		core.origOnInputArea = core.onInput;
	}
	core.areaPhase = null; core.areaRows = []; core.areaDir = ""; core.areaCool = 0; core.areaCoolName = ""; core.areaCreated = "";
	core.areaNote = function (m) { if (typeof ClaudeLog != "undefined") ClaudeLog.note(m); };
	core.areaMatch = function (cmd) { return cmd ? cmd.match(/^\.триг обл(?:асть)? (?:с|соз\S*|создать) (\S+)/) : null; };

	core.areaSave = function (name, repopMin, remainSecs) {
		try {
			var now = (new Date()).getTime();
			var exp = remainSecs > 0 ? now + remainSecs * 1000 : now + repopMin * 60000 + 30000;
			var f = fso.OpenTextFile("areas/area_timers.txt", 8, true);
			f.WriteLine(name + "|" + now + "|" + repopMin + "|" + exp);
			f.Close();
		} catch (e) {}
	};

	core.nextStep = function () {
		if (!this.areaPhase && zons.length > seekstep) {
			var m = this.areaMatch(zons[seekstep]);
			if (m) { this.areaStart(m[1]); return; }
		}
		return this.origNextStepArea();
	};

	core.areaStart = function (dir) {
		this.areaDir = dir; this.areaRows = []; this.areaPhase = "list"; this.waitFlag = true;
		seekstep++;
		this.areaNote("AREA_CHECK dir=" + dir + " zone=" + zonename);
		jmc.send("обл");
		jmc.setTimer(154, 30);
	};
	core.areaDecide = function () {
		jmc.killTimer(154);
		var name = AREA_NAMES[zonename], row = null, i;
		for (i = 0; i < this.areaRows.length; i++) {
			var r = this.areaRows[i];
			if (!name || r.name == name) {
				if ((this.areaWaited && name) || /удалите вручную|готов/i.test(r.status + " " + r.timer)) { row = r; break; }
			}
		}
		this.areaWaited = false;
		if (row) {
			this.areaPhase = "delete";
			this.areaNote("AREA_DELETE " + row.name + " (" + row.status + " / " + row.timer + ")");
			jmc.send("обл удал " + this.areaDir);
			jmc.setTimer(155, 25);
		} else {
			this.areaCreate();
		}
	};
	core.areaCreate = function () {
		this.areaPhase = "create"; this.areaCool = 0; this.areaCreated = "";
		jmc.send("обл с " + this.areaDir);
		jmc.setTimer(156, 25);
	};
	core.areaAfterCreate = function () {
		jmc.killTimer(156);
		if (this.areaCool > 0 && typeof AREA_NOWAIT != "undefined" && AREA_NOWAIT[zonename]) {
			this.areaPhase = null;
			this.BotInZone = true;
			this.areaNote("AREA_NOWAIT zone=" + this.areaCoolName + " cooldown=" + this.areaCool + " -> walking in");
			this.wait(10);
			return;
		}
		if (this.areaCool > 0) {
			this.BotInZone = false;
			var secs = this.areaCool + 30; this.areaWaited = true;   // Claude 13.11 (слова пользователя): КД зоны + 30 с, потом принудительно обл удал
			seekstep--;                              // the area line runs again after the wait
			this.areaPhase = null;
			this.areaNote("AREA_WAIT secs=" + secs + " zone=" + this.areaCoolName);
			this.areaSave(this.areaCoolName, 0, secs);
			jmc.showme("-:- [Область '" + this.areaCoolName + "': ждём " + secs + " с]");
			this.wait(Math.min(secs * 10, 9000));
			return;
		}
		this.areaNote("AREA_CREATED " + this.areaCreated);
		this.areaPhase = "post"; this.areaRows = [];
		jmc.send("обл");
		jmc.setTimer(157, 30);
	};
	core.areaPost = function () {
		jmc.killTimer(157);
		var repop = 0, i;
		for (i = 0; i < this.areaRows.length; i++) { if (this.areaRows[i].name == this.areaCreated) repop = this.areaRows[i].repop; }
		if (this.areaCreated) this.areaSave(this.areaCreated, repop, 0);
		this.areaPhase = null;
		this.wait(10);
	};

	core.onIncoming = function (sTextLine) {
		var r = this.origOnIncomingArea(sTextLine);
		var s = rmcolor(sTextLine);
		if (this.areaPhase == "list" || this.areaPhase == "post") {
			var m = s.match(/^\s*(\S.*?)\s+(\d+)\s+(.+?)\s{2,}(\S+)\s+(\d+)\s+(.+?)\s*$/);
			if (m) this.areaRows.push({status: m[1], num: m[2], name: m[3], leader: m[4], repop: parseInt(m[5], 10), timer: m[6]});
		}
		if (this.areaPhase == "create") {
			var c = s.match(/^Вы сможете создать новый экземпляр зоны '(.+)' через (?:(\d+) мин\S*)?\s*(?:(\d+) сек\S*)?/);
			if (c) { this.areaCool = parseInt(c[2] || "0", 10) * 60 + parseInt(c[3] || "0", 10); this.areaCoolName = c[1]; }
			var k = s.match(/^Создан экземпляр зоны '(.+)'/);
			if (k) this.areaCreated = k[1];
		}
		return r;
	};
	core.onTimer = function (idTimer) {
		var t = jmc.event;
		if (t == 154) { this.areaDecide(); return; }
		if (t == 155) { jmc.killTimer(155); this.areaCreate(); return; }
		if (t == 156) { this.areaAfterCreate(); return; }
		if (t == 157) { this.areaPost(); return; }
		return this.origOnTimerArea(idTimer);
	};
	core.onInput = function (sTextLine) {
		if (sTextLine == ".бот обл") {
			try {
				var f = fso.OpenTextFile("areas/area_timers.txt", 1);
				var now = (new Date()).getTime();
				while (!f.AtEndOfStream) {
					var p = f.ReadLine().split("|");
					if (p.length < 4) continue;
					var left = Math.round((parseInt(p[3], 10) - now) / 60000);
					jmc.showme("-:- " + p[0] + ": " + (left > 0 ? "ещё " + left + " мин" : "срок вышел"));
				}
				f.Close();
			} catch (e) { jmc.showme("-:- Таймеров областей пока нет"); }
			return;
		}
		return this.origOnInputArea(sTextLine);
	};
})();
jmc.showme("-:- AreaGuard loaded");
